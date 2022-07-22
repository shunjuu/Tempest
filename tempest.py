import json
import metsuke
import os
import shikyou
import signal
import subprocess
import rabbitpy
import sys
import tempfile
import time

from ayumi import Ayumi
from config import settings
from pathlib import Path
from retry import retry

# Signal handler


def sig_handler(sig, frame):
    Ayumi.warning("SIG command {} detected, exiting...".format(
        sig), color=Ayumi.LRED)
    sys.exit()


# Add in SIGKILL handler
signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)

@retry(delay=60, backoff=1.5, max_delay=3600, logger=Ayumi.get_logger())
def consume():
    try:
        with rabbitpy.Connection('amqp://{username}:{password}@{host}:{port}/{vhost}'.format(
            username=settings.get('RABBITMQ_USERNAME'),
            password=settings.get('RABBITMQ_PASSWORD'),
            host=settings.get('RABBITMQ_HOST'),
            port=settings.get('RABBITMQ_PORT'),
            vhost=settings.get('RABBITMQ_VHOST')
        )) as conn:
            with conn.channel() as channel:
                channel.enable_publisher_confirms()
                Ayumi.set_rabbitpy_channel(channel)
                queue = rabbitpy.Queue(channel, settings.get('TEMPEST_RABBITMQ_QUEUE'))
                queue.declare(passive=True)
                Ayumi.info("Now listening for messages from AMQP provider.", color=Ayumi.YELLOW)

                for message in queue.consume(prefetch=1):
                    try:
                        job = json.loads(message.body.decode('utf-8'))
                    except json.JSONDecodeError:
                        Ayumi.warning("Received a job that is invalid json, not processing.", color=Ayumi.LRED)
                        message.reject()
                        continue

                    Ayumi.info("Received a new job: {}".format(json.dumps(job)), color=Ayumi.CYAN)
                    if metsuke.validate(job):
                        Ayumi.debug("Loaded show: {}".format(job['show']))
                        Ayumi.debug("Loaded episode: {}".format(job['episode']))
                        Ayumi.debug("Loaded filesize: {}".format(job['filesize']))
                        Ayumi.debug("Loaded sub type: {}".format(job['sub']))

                        metsuke_job = metsuke.Job(
                            job['show'], job['episode'], job['filesize'], job['sub'])
                        metsuke_job_hard = metsuke.Job(
                            job['show'], job['episode'].replace("mkv", "mp4"), job['filesize'], job['sub'])


                        with tempfile.NamedTemporaryFile(suffix=".conf", mode="w+b") as rconf, tempfile.TemporaryDirectory() as tempdir:

                            Ayumi.debug("Opening context managed rclone config file under path: {}.".format(rconf.name))
                            Ayumi.debug("Opening context managed rclone temporary directory under path: {}".format(tempdir))

                            # Write the rclone file
                            rconf.write(str.encode(settings.get("RCLONE_CONFIG_FILE")))
                            rconf.flush()  # YOU MUST FLUSH THE FILE SO RCLONE CAN READ IT!
                            Ayumi.debug("Configurations written to temporary file. Size is {} bytes.".format(rconf.tell()))

                            try:
                                temp = Path(shikyou.download(metsuke_job, settings.get('TEMPEST_RCLONE_DOWNLOAD_SOURCES'), tempdir, rconf.name, settings.get("RCLONE_FLAGS", "")))
                                temp_abspath = str(temp.resolve())
                                encode_command = [
                                        "ffmpeg",
                                        "-i",
                                        temp_abspath,
                                        "-vf",
                                        "subtitles={}:force_style='FontName=Open Sans Semibold:fontsdir=/opt/fonts'".format(temp_abspath)
                                        ]

                                # Get the string of flags user provided in config, or default to empty string
                                user_ffmpeg_flags = settings.get('TEMPEST_FFMPEG_ENCODE_FLAGS', "").split(" ")
                                for flag in user_ffmpeg_flags:
                                    if flag:
                                        encode_command.append(flag)

                                encode_command.append(tempdir + "/temp.mp4")

                                Ayumi.info("Executing encode command: {}".format(encode_command))
                                subprocess.run(encode_command)
                                shikyou.upload(metsuke_job_hard, settings.get("TEMPEST_RCLONE_UPLOAD_DESTS"), tempdir + "/temp.mp4", rconf.name, settings.get("RCLONE_FLAGS", ""))

                            except shikyou.ShikyouResponseException:
                                Ayumi.critical("Rclone threw an unexpected response code, rejecting.", color=Ayumi.RED)
                                message.reject()
                                continue
                            except shikyou.ShikyouTimeoutException:
                                Ayumi.warning("Rclone timed out whilhe executing, nacking.", color=Ayumi.RED)
                                message.nack()
                                continue

                            try:
                                job = {
                                    "show": metsuke_job_hard.show,
                                    "episode": metsuke_job_hard.episode,
                                    "filesize": os.path.getsize(tempdir + "/temp.mp4"),
                                    "sub": "hardsub"
                                }
                                pub_msg = rabbitpy.Message(channel, job)
                                if pub_msg.publish(settings.get('TEMPEST_PUBLISH_EXCHANGE')):
                                    Ayumi.info("Job successfully published to RabbitMQ", color=Ayumi.LGREEN)
                                else:
                                    Ayumi.warning("Job unsuccessfully published to RabbitMQ", color=Ayumi.LRED)
                                    raise Exception()
                            except:
                                Ayumi.warning("Job unsuccessfully published to RabbitMQ", color=Ayumi.LRED)
                                raise Exception()

                    Ayumi.info("Completed processing this message for {}".format(job['episode']), color=Ayumi.LGREEN)
                    message.ack()

    except rabbitpy.exceptions.AMQPConnectionForced:

        Ayumi.rabbitpy_channel = None
        Ayumi.critical("Operator manually closed RabbitMQ connection, shutting down.", color=Ayumi.RED)
        # Use return for now because in some cases, calling exit() may invoke the retry() header.
        return

if __name__ == "__main__":
    consume()
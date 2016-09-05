import hmac
import hashlib

from errbot import BotPlugin, webhook
from cmlCiscoSparkSDK import sparkapi


class CiscoSparkWebhook(BotPlugin):

    @webhook('/errbot/spark', raw=True)
    def errbot_spark(self, raw):

        signature = hmac.new(self._bot.webhook_secret.encode('utf-8'), raw.body.read(), hashlib.sha1).hexdigest()

        if signature != raw.get_header('X-Spark-Signature'):
            self.log.debug("X-Spark-Signature failed. Webhook will NOT be processed")

        else:
            webhook_event = sparkapi.Webhook(raw.json)

            if webhook_event.actorId == self._bot.bot_identifier.id:
                self.log.debug("Message created by bot...ignoring")

            else:

                # Need to load to complete message from Spark as the webhook message only includes IDs
                message = self._bot.get_message_using_id(webhook_event.data.id)

                # We only build superficial objects using the ID as loading the full person/room details would
                # significantly delay the processing of the message
                person = self._bot.create_person_using_id(webhook_event.data.personId)
                room = self._bot.create_room_using_id(webhook_event.data.roomId)
                
                occupant = self._bot.get_occupant_using_id(person=person, room=room)

                msg = self._bot.create_message(body=message.text, frm=occupant, to=room,
                                               extras={'roomType': webhook_event.data.roomType})

                # Force the bot to process the message and our job is done!
                self._bot.process_message(msg)

        return "OK"

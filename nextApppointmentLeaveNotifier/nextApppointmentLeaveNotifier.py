import appdaemon.plugins.hass.hassapi as hass
import datetime
import messages
import globals

#
# App which notifies the user to start to the next appointment
#
#
# Args:
# sensor: sensor to watch. example: sensor.calc_leave_time
# notify_input_boolean: input_boolean determining whether to notify. example: input_boolean.announce_time_to_leave
# notify_name: Who to notify. example: group_notifications
# destination_name_sensor: Sensor which holds the Destination name to use in notification. example: sensor.cal_next_appointment_location
# travel_time_sensor: sensor which holds the travel time. example: sensor.travel_time_next_appointment_location
# message_<LANG>: localized message to use in notification
#
# Release Notes
#
# Version 1.4.1:
#   Fix google maps url message
#
# Version 1.4:
#   Don't include Google Maps Link in Notification for Alexa
#
# Version 1.3:
#   Also notify when Notification time is in the past
#
# Version 1.2:
#   use Notify App
#
# Version 1.1:
#   Using globals, message now directly in own yaml instead of message module
#
# Version 1.0:
#   Initial Version

class NextApppointmentLeaveNotifier(hass.Hass):

    def initialize(self):

        self.listen_state_handle_list = []
        
        self.sensor = globals.get_arg(self.args,"sensor")
        self.notify_input_boolean = globals.get_arg(self.args,"notify_input_boolean")
        self.notify_name = globals.get_arg(self.args,"notify_name")
        self.destination_name_sensor = globals.get_arg(self.args,"destination_name_sensor")
        self.travel_time_sensor = globals.get_arg(self.args,"travel_time_sensor")
        self.message = globals.get_arg(self.args,"message")
        self.message_google_link = globals.get_arg(self.args,"message_google_link")

        self.timer_handle = None

        self.google_source_url = "http://maps.google.com/maps?q="

        self.notifier = self.get_app('Notifier')

        #Used to check of user got already notified for this event
        self.location_of_last_notified_event = ""
        destination_name = self.get_state(self.destination_name_sensor)
        self.log("destination_name_sensor: {} ".format(destination_name))
        if destination_name != "unknown" and destination_name != "None":
            notification_time = datetime.datetime.strptime(self.get_state(self.sensor),"%Y-%m-%d %H:%M")
            if self.get_state(self.travel_time_sensor) != "unknown":
                try:
                    self.timer_handle = self.run_at(self.notify_user,notification_time)
                    self.log("Will notify at {}".format(notification_time))
                except ValueError:
                    self.log("Notification time is in the past")

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.sensor))

    def state_change(self, entity, attributes, old, new, kwargs):
        try:
            self.cancel_timer(self.timer_handle)
            self.timer_handle = None
        except AttributeError:
            #Timer was not set
            pass
        #Parse time string from sensor. For parsing information look at http://strftime.org/
        destination_name = self.get_state(self.destination_name_sensor)
        self.log("destination_name_sensor: {} ".format(destination_name))
        if destination_name != "unknown" and destination_name != "None":
            notification_time = datetime.datetime.strptime(self.get_state(self.sensor),"%Y-%m-%d %H:%M")
            if self.get_state(self.travel_time_sensor) != "unknown":
                try:
                    self.timer_handle = self.run_at(self.notify_user,notification_time)
                    self.log("Will notify at {}".format(notification_time))
                except ValueError:
                    self.log("Notification time is in the past")
                    self.timer_handle = self.run_at(self.notify_user,datetime.datetime.now())

    def notify_user(self, *kwargs):
        if self.get_state(self.notify_input_boolean) == "on":
            location_name = self.get_state(self.destination_name_sensor)
            if self.location_of_last_notified_event == location_name:
                self.log("User already got notified for {}".format())
            else:
                google_maps_url = self.google_source_url + location_name.replace(" ","+")
                self.log("Notify user")
                self.notifier.notify(self.notify_name, self.message.format(location_name,self.get_state(self.travel_time_sensor)))
                self.notifier.notify(self.notify_name, self.message_google_link.format(google_maps_url), useAlexa=False)
                self.location_of_last_notified_event = location_name
        else:
            self.log("Notification is turned off")

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)
        if self.timer_handle != None:
            self.cancel_timer(self.timer_handle)
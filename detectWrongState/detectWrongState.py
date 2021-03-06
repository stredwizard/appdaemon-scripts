import appdaemon.plugins.hass.hassapi as hass
import globals
#
# App which notifies of wrong states based on a state change
#
# Args:
#
# app_switch: on/off switch for this app. example: input_boolean.turn_fan_on_when_hot
# entities_on (optional): list of entities which should be on
# entities_off (optional): list of entities which should off
# trigger_entity: entity which triggers this app. example: input_boolean.is_home
# trigger_state: new state of trigger_entity which triggers this app. example: "off"
# after_sundown (optional): Only trigger after sundown. example: True
# message_<LANG>: message to use in notification
# message_off_<LANG>: message to use in notification
# message_reed_<LANG>: message to use in notification
# message_reed_off_<LANG>: message to use in notification
# notify_name: who to notify. example: group_notifications
# use_alexa: use alexa for notification. example: False
#
# Release Notes
#
# Version 2.0:
#   Renamed to detectWrongState, notification optional
#
# Version 1.9:
#   check unavailable when using get_state
#
# Version 1.8:
#   check None when using get_state
#
# Version 1.7:
#   check for != off instead of == on
#
# Version 1.6.1:
#   fix wrong key access for attributes
#
# Version 1.6:
#   garage_door to device_classes of reed sensors
#
# Version 1.5:
#   distinguish normal and reed switches by device_class
#
# Version 1.4.1:
#   fix wrong assignment of app_switch
#
# Version 1.4:
#   Generalize to detectWrongState
#
# Version 1.3:
#   use Notify App
#
# Version 1.2:
#   message now directly in own yaml instead of message module
#
# Version 1.1:
#   Using globals and app_switch
#
# Version 1.0:
#   Initial Version


class DetectWrongState(hass.Hass):

    def initialize(self):
        self.listen_state_handle_list = []

        self.app_switch = globals.get_arg(self.args, "app_switch")
        try:
            self.entities_on = globals.get_arg_list(self.args, "entities_on")
        except KeyError:
            self.entities_on = []
        try:
            self.entities_off = globals.get_arg_list(self.args, "entities_off")
        except KeyError:
            self.entities_off = []
        try:
            self.after_sundown = globals.get_arg(self.args, "after_sundown")
        except KeyError:
            self.after_sundown = None
        self.trigger_entity = globals.get_arg(self.args, "trigger_entity")
        self.trigger_state = globals.get_arg(self.args, "trigger_state")
        try:
            self.message = globals.get_arg(self.args, "message")
        except KeyError:
            self.message = None
        try:
            self.message_off = globals.get_arg(self.args, "message_off")
        except KeyError:
            self.message_off = None
        try:
            self.message_reed = globals.get_arg(self.args, "message_reed")
        except KeyError:
            self.message_reed = None
        try:
            self.message_reed_off = globals.get_arg(self.args, "message_reed_off")
        except KeyError:
            self.message_reed_off = None
        try:
            self.notify_name = globals.get_arg(self.args, "notify_name")
        except KeyError:
            self.notify_name = None
        try:
            self.use_alexa = globals.get_arg(self.args, "use_alexa")
        except KeyError:
            self.use_alexa = False

        self.notifier = self.get_app('Notifier')

        self.listen_state_handle_list.append(self.listen_state(self.state_change, self.trigger_entity))

    def state_change(self, entity, attribute, old, new, kwargs):
        if self.get_state(self.app_switch) == "on":
            if new != "" and new == self.trigger_state:
                if(
                        self.after_sundown is None
                        or (
                            (self.after_sundown and self.sun_down())
                            or self.after_sundown is not False
                        )
                ):
                    # entities_off
                    for entity in self.entities_off:
                        full_state = self.get_state(entity, attribute="all")
                        if full_state is not None:
                            attributes = full_state["attributes"]
                            self.log("full_state: {}".format(full_state))
                            if(
                                full_state["state"] != "off"
                                and full_state["state"] != "unavailable"
                                and "device_class" in attributes
                                and (
                                    attributes["device_class"] == "window"
                                    or attributes["device_class"] == "door"
                                    or attributes["device_class"] == "garage_door"
                                )
                            ):
                                if self.message_reed is not None:
                                    self.log(self.message_reed.format(self.friendly_name(entity)))
                                    if self.notify_name is not None:
                                        self.notifier.notify(
                                            self.notify_name,
                                            self.message_reed.format(
                                                self.friendly_name(entity)),
                                            useAlexa=self.use_alexa)
                            elif(
                                full_state["state"] != "off"
                                and full_state["state"] != "unavailable"
                            ):
                                self.turn_off(entity)
                                if self.message is not None:
                                    self.log(self.message.format(self.friendly_name(entity)))
                                    if self.notify_name is not None:
                                        self.notifier.notify(
                                            self.notify_name,
                                            self.message.format(
                                                self.friendly_name(entity)),
                                            useAlexa=self.use_alexa)
                    # entities_on
                    for entity in self.entities_on:
                        full_state = self.get_state(entity, attribute="all")
                        attributes = full_state["attributes"]
                        self.log("full_state: {}".format(full_state))
                        if (
                            full_state["state"] == "off"
                            and "device_class" in attributes
                            and (
                                attributes["device_class"] == "window"
                                or attributes["device_class"] == "door"
                                or attributes["device_class"] == "garage_door"
                            )
                        ):
                            if self.message_reed_off is not None:
                                self.log(self.message_reed_off.format(self.friendly_name(entity)))
                                if self.notify_name is not None:
                                    self.notifier.notify(
                                        self.notify_name,
                                        message=self.message_reed_off.format(
                                            self.friendly_name(entity)),
                                        useAlexa=self.use_alexa)
                        elif full_state["state"] == "off":
                            self.turn_on(entity)

                            if self.message_off is not None:
                                self.log(self.message_off.format(self.friendly_name(entity)))
                                if self.notify_name is not None:
                                    self.notifier.notify(
                                        self.notify_name,
                                        message=self.message_off.format(
                                            self.friendly_name(entity)),
                                        useAlexa=self.use_alexa)

    def terminate(self):
        for listen_state_handle in self.listen_state_handle_list:
            self.cancel_listen_state(listen_state_handle)

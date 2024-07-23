[![Stargazers repo roster for @jdeath/Hubspace-Homeassistant](https://git-lister.onrender.com/api/stars/jdeath/Hubspace-Homeassistant?limit=30)](https://github.com/jdeath/Hubspace-Homeassistant/stargazers)

Please ask support questions in homeassistant forums: https://community.home-assistant.io/t/add-support-for-hubspace-by-afero/306645

### Background
HubSpace is reliant on a cloud connection which means this integration could break at any point. Not all
devices may be supported with and developer time will be required to add new devices.

### Breaking Change:
Configuration is done through the `Add Integrations` rather than configuration.yaml.

Now supports services for capability not provided by the integration. See Services section below

Thanks to @dloveall this release will automatically discover most devices. Specifying your friendlynames is still possible, but this now finds most models attached to your account. There may be some that are not auto discovered.

Since some of the internals were changed, so your light name may change. For instance, light.friendlyname might turn into light.friendlyname_2

To solve this, go to Settings->Devices and Services->Entities
find the light.friendlyname and delete it. then find the light.friendlyname_2 and rename it light.friendlyname

### Information :
This integration talks to the HubSpace API to set and retrieve states for all
of your registered devices. After performing the configuration, it will
register all devices unless specified by `friendlyNames` and/or `roomNames`. Once
the devices are discovered, it will determine device capability and show
correctly within Home Assistant.

_Thanks to everyone who starred my repo! To star it click on the image below, then it will be on top right. Thanks!_

[![Stargazers repo roster for @jdeath/Hubspace-Homeassistant](https://reporoster.com/stars/jdeath/Hubspace-Homeassistant)](https://github.com/jdeath/hubspace-homeassistant/stargazers)

### Installation


#### UI (Preferred)
Add this repo as a custom repository in [HACS](https://hacs.xyz/). Add the hubspace integration.

Clicking this badge should add the repo for you:
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jdeath&repository=Hubspace-Homeassistant&category=integration)

#### Manual
Manually add repo:
Adding a custom repo directions `https://hacs.xyz/docs/faq/custom_repositories/`
Use the custom repo link `https://github.com/jdeath/Hubspace-Homeassistant`
Select the category type `integration`
Then once it's there (still in HACS) click the INSTALL button

Manual method: copy the hubspace/ folder in the repo to `<config_dir>/custom_components/hubspace/`.

### Configuration
After HubSpace has been added through HACs and Home Assistant has been removed, the
configuration continues within the UI like other integrations. First select `Settings`
on the navigation bar, then select `Devices & services`, ensure you are on the
`Integrations` tab, then finally select `ADD INTEGRATION` at the bottom right
of the page. Search for `HubSpace` and enter your username and password and
click `SUBMIT`. After the credentials are authentication, you will be
prompted for automatic discovery, or manually select devices / rooms.



### Troubleshooting

Be sure you are specifcally adding the freindlynames of your lights in the configruation.yaml. The autoscan does not work for all, so you **must add the friendlyname into the configuration.yaml before requesting help**.

If you are having problems, first try renaming the device name in the App. Do not use spaces or special characters like & in the name of your lights. This code may also fail with names like Office, Bedroom, Fireplace. Make it something unique and not the same as a group. Hopefully this has been fixed, but still could be issues.

Also be sure to check the friendlyname of your light. It must match *exactly* as shown in the app, including uppercase/lowercase. Requiring the case to match may be a recent change by Hubspace

If you have a combo fan/light, it is confirmed to work best if you do not use friendlyname or roomnames. The automatic scan should pick it up. If you must use friendlyname, just add the name of the parent device from the hubspace app. Do not add separate names for the light and fan. The integration will make a light.friendlyname (the light) and light.friendlyname_fan (the fan). Better handling is a work in progress.

If you have an outlet or transfomer, just add the name of the parent device from the hubspace app. Do not add the separate outlet's/transformer's names. The integration will figure it out and make entities called light.friendlyname_outlet_X or light.friendlyname_transformer_X where X is 1,2,3 depending on how many outputs in has.

Do not use a special character, like @ as the first character of your password. Quoting your password in the yaml might be nessesary, or move the special character to the middle of your password.

This integrations polls the cloud for updates. So, it will take time to register a change in the UI. Just wait 30-60 seconds and it should sync up. If anyone can offer a solution, let me know.
### Support for a new model

Please make a github issue if you want support for a new model. I will need your help to test.

Easiest way to help is to download the Testhubspace.py (https://raw.githubusercontent.com/jdeath/Hubspace-Homeassistant/main/TestHubspace.py) and run it (may need to run `pip install requests` or 'python3 -m pip install requests' or `apk add py3-requests` first). It will prompt you for your hubspace username and password. It will output data, which you should copy and paste into the GitHub issue. The output has been anonymized, personal information has been removed or randomized.

To run right in homeassistant: Install the Advanced SSH & Web Terminal addon if you have not already
Start a terminal session from your homeassistant and go to homeassistant directory (used to be called config)
`cd homeassistant`
download the file:
`wget https://raw.githubusercontent.com/jdeath/Hubspace-Homeassistant/main/TestHubspace.py`
install requests module if not alread installed:
`pip install requests`
run script:
`python TestHubspace.py`

If cannot run python3, get the entity loaded in homeassistant. Set debug:true in configuration as shown above. Click on the entity in homeassistant, expand the attributes, and send me the model and debug fields. This information is *not* anonymized. Best to PM me these on the homeassistant forums, as there is semi-private information in them. Send me these fields with the light set to on/off/etc (you may need to use the app). If that doesn't work, I may need better debug logs. Then you can add in your configuration.yaml (not in the hubspace section). Then you email me your homassistant.log
```
logger:
  default: error
  logs:
    custom_components.hubspace: debug
```
you may already have the top two lines, just need to add the buttom two

### Fan Support
If you have a fan, just add the name of the parent device from the hubspace app. Do not add separate names for the light and fan. This is just how it works. Users have said the autoscan works best, so do not use friendlyname or roomnames

Since the fan is implemented as a light with a dimmer, you can use a template to make it appear as a fan. Replace "light.ceilingfan_fan" below with the name of your fan. Confirm you can use the fan before you make the template.  This is optional, only if you really want homeassistant to show the light as a fan entity. This was provided by a user, no support possible. Again, this is optional, only do this once you can control the fan entity normally before hand.
```
# Example configuration.yaml entry
fan:
  - platform: template
    fans:
      living_room_fan:
        friendly_name: "Fan"
        value_template: "{{ states('light.ceilingfan_fan') }}"
        percentage_template: "{{ ((state_attr('light.ceilingfan_fan', 'brightness') | int(0)) / 255 * 100) | int }}"
        turn_on:
          service: homeassistant.turn_on
          entity_id: light.ceilingfan_fan
        turn_off:
          service: homeassistant.turn_off
          entity_id: light.ceilingfan_fan
        set_percentage:
          service: light.turn_on
          entity_id: light.ceilingfan_fan
          data_template:
            brightness: "{{ ( percentage / 100 * 255) | int }}"
        speed_count: 4
```

### Transformer Support
System-wide watt and voltage setting available as attribute in the first output entity. Get watts in lovelace with a card with this entry:
```
- entity: Friendlyname_transformer_1
  type: attribute
  attribute: watts
  ```

## Lock support
The lock "light" will also report the battery status and last operation in the attributes. Optional: If you want to have the light show up as a lock in HA, make a template (but the battery is only available on the light). In your configuration.yaml add this (assumes your light is light.door_lock), click the magnifying glass in top right of HA, then hit >Temp to reload the template entity . Again, this is optional, only do this once you can control the light entity normally before hand.

Belore example assumes the friendlyname of your lock is door_lock (so it true homeassistant name is light.door_lock)
```
lock:
  - platform: template
    name: Back Door Lock
    optimistic: true
    unique_id: "BackDoorLockTemplate123"
    value_template: "{{ is_state('light.door_lock', 'on') }}"
    lock:
      service: light.turn_on
      target:
        entity_id: light.door_lock
    unlock:
      service: light.turn_off
      target:
        entity_id: light.door_lock
```

### Services:
The integration now has the capability to send a service. You may want this if there is a capability that is not supported by the integration. However, **do not use this service, if just want to turn lights on/off or anything else supported by the standard light service** (rgb, brightness, colortemp, etc) use the standard light.turn_on , light.turn_off for that.`https://www.home-assistant.io/integrations/light/#service-lightturn_on`.
For example, if you want to send the rainbow effect to your rgb light:
```
service: hubspace.send_command
data:
  value: "rainbow"
  functionClass: color-sequence
  functionInstance: custom
target:
  entity_id: light.yourlightname
  ```
For example, if you want to send the comfort breeze effect to your fan:
```
service: hubspace.send_command
data:
  value: "enabled"
  functionClass: toggle
  functionInstance: comfort-breeze
target:
  entity_id: light.yourlightname
  ```
You do this is the Developers Tools -> Services window. The GUI can be used to choose an entity.

How do you find out what the value, functionClass and functionInstance should be? Look at the output of running TestHubspace.py on your device. If you look around, you will see what your light supports in the "values" field. See https://github.com/jdeath/Hubspace-Homeassistant/blob/main/sample_data/11A21100WRGBWH1.json#L686 . The functionInstance is optional, as not all commands require it. There are some example outputs of TestHubspace.py in the sample_data/ directory of the repo. If you cannot run the TestHubspace.py, then turn on debugging (debug: true in your light: setup). Change the setting in the app, and look at the entity attributes in homeassistant. You should be able to see an entry that has the value, functionClass, etc.

You can make a button in lovelace to send any command you want. The lovelace GUI will do most of this, but not fill in the data correctly. A working example to turn on rainbow effect:
```
show_name: true
show_icon: true
type: button
tap_action:
  action: call-service
  service: hubspace.send_command
  data:
    value: "rainbow"
    functionClass: color-sequence
    functionInstance: custom
  target:
    entity_id: light.yourlightname
```
[![Star History Chart](https://api.star-history.com/svg?repos=jdeath/Hubspace-Homeassistant&type=Date)](https://star-history.com/#jdeath/Hubspace-Homeassistant&Date)

# Robot Class System

## Introduction
The robot class system allows robots can have different capabilities. Normally one capability will be increased while another is decreased. For example, a robot may take less damage (better) but have a lower max speed (worse). Robots are in the "default" class unless a different class is specified.

## How To Specify a Class

Classes must be enabled by adding the ```-allowclasses``` option to the server. Once enabled, robots can specify a class in the joinRequest message. For example:

```{ 'type': 'joinRequest', 'name': 'Super Robot V3', 'class': 'heavy' }```

## Classes

### default
<img src="images/class_default.png" width="60%">

---

### heavy
<img src="images/class_heavy.png" width="60%">

---

### light
<img src="images/class_light.png" width="60%">

---

### machinegun
<img src="images/class_machinegun.png" width="60%">

---

### sniper
<img src="images/class_sniper.png" width="60%">

---

### turtle
<img src="images/class_turtle.png" width="60%">
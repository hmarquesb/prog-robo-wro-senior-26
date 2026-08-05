#!/usr/bin/env pybricks-micropython
from setup import sensor_esq, sensor_dir, motor_A, motor_B, motor_C, motor_D, ev3, wait
import setup as s
import movimento as m
import linha as lin
import carrinho as c

motor_D.run_time(500,1200,then=s.Stop.COAST)
#motor_D.run_time(500,1200,then=s.Stop.COAST)

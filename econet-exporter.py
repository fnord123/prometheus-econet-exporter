# Prometheus econet Exporter
#
# (c) David Putzolu

from prometheus_client import start_http_server, Gauge
import requests
import pyeconet
import sys
import time
from time import sleep
from envargparse import EnvArgParser, EnvArgDefaultsHelpFormatter
from pyeconet import EcoNetApiInterface
from pyeconet.equipment import EquipmentType
import asyncio
from pyeconet import EcoNetApiInterface
from decimal import Decimal



class econetPrometheusExporter:
  def __init__(self):
    try:
      self._args = {}
      self.main()
    except Exception as e:
      print('Error - {}'.format(e))
      sys.exit(1)

  def process_args(self):
    parser = EnvArgParser\
      ( prog="Econet Prometheus Exporter"
      , formatter_class=EnvArgDefaultsHelpFormatter
      )
    parser.add_argument\
      ( '--interval_seconds'
      , required=False
      , env_var="INTERVAL_SECONDS"
      , type=int
      , nargs="?"
      , default=300
      , const=True
      , help="How often in seconds data should be pulled from the Econet servers and exported to Prometheus"
      )
    parser.add_argument\
      ( '--port'
      , required=False
      , env_var="EXPORTER_PORT"
      , type=int
      , default=8000
      , const=True
      , nargs="?"
      , help="Port number the exporter should bind to"
      )
    parser.add_argument\
      ( '--verbose'
      , required=False
      , env_var="EXPORTER_VERBORSE"
      , action='store_true'
      , default=False
      , help="Enable verbose debug outputs"
      )
    parser.add_argument\
      ( '--device_name'
      , required=False
      , env_var="DEVICE_NAME"
      , nargs="?"
      , default="Water Heater"
      , const=True
      , help="Name to attach to the metric uploaded to Prometheus"
      )
    parser.add_argument\
      ( '--email'
      , required=False
      , env_var="ECONET_EMAIL"
      , nargs="?"
      , default="nobody@gmail.com"
      , const=True
      , help="Email address for the Econet account"
      )
    parser.add_argument\
      ( '--password'
      , required=False
      , env_var="ECONET_PASSWORD"
      , nargs="?"
      , default="enterPasswordHere"
      , const=True
      , help="Password for the econet account"
      )
      
    self._args = parser.parse_args()
    if self._args.verbose:
      print(self._args)

  def timestamped_output(self, output):
    print("%s: %s" % (time.strftime("%H:%M:%S"), output))

  def update_field(self, field_value):
    self._power.labels(self._args.device_name).set(field_value)
    if self._args.verbose:
      self.timestamped_output( \
        "%s is using %s watts" % (self._args.device_name, field_value))

  async def main_async(self):
    api = await EcoNetApiInterface.login( \
      self._args.email, password=self._args.password)
    all_equipment = await api.get_equipment_by_type( \
      [EquipmentType.WATER_HEATER, EquipmentType.THERMOSTAT])
    # TODO: Add something smarter than just grabbing the first item
    equipment = next(iter(next(iter(all_equipment.values()))))
    await equipment.get_energy_usage()
    kwh = \
      Decimal(equipment.energy_usage).quantize(Decimal('1.000'))
    if self._args.verbose:
      self.timestamped_output( \
        "Initial kWh consumed is %s" % kwh)
    prior_kwh = kwh
    while True:
      if kwh < prior_kwh:
        incremental_kwh = kwh
      else:
        incremental_kwh = kwh - prior_kwh
        prior_kwh = kwh
      # Usage is measured in kWh, but we sample every INTERVAL_SECONDS,
      # so we need to factor that in.
      if self._args.verbose:
        self.timestamped_output( \
          "Latest kWh reading is %s" % kwh)
        self.timestamped_output( \
          "Incremental kWh consumption is %s" % incremental_kwh)          
      averaged_power = incremental_kwh * \
        Decimal(1000.0 * 60.0 * 60.0).quantize(Decimal('1.000')) \
          / Decimal(self._args.interval_seconds).quantize(Decimal('1.000'))
      averaged_power = averaged_power.quantize(Decimal('1.0'))
      self.update_field(averaged_power)
      sleep(self._args.interval_seconds)
      await equipment.get_energy_usage()
      kwh = \
        Decimal(equipment.energy_usage).quantize(Decimal('1.000'))

  def main(self):
    self.process_args()
    self._power = \
      Gauge('power', 'Instantaneous power consumption', ['device'])
    start_http_server(self._args.port)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(self.main_async())

    exit()
    while True:
      self.collect()
      sleep(self._args.interval)

econetPrometheusExporter()

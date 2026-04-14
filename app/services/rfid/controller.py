"""
Docstring for app.services.rfid.controller
This module will be used for custom logic.
"""

from smartx_rfid.devices import DeviceManager
from smartx_rfid.utils import TagList
import logging
from .integration import Integration
import asyncio
from app.core import settings
from smartx_rfid.schemas.tag import WriteTagValidator


class Controller:
	def __init__(self, devices: DeviceManager, tags: TagList, integration: Integration):
		self.tags = tags
		self.devices = devices
		self.integration = integration
		self.serial: int = 0

	# [ EVENTS ]
	def on_event(self, name: str, event_type: str, event_data):
		asyncio.create_task(
			self.integration.on_event_integration(
				name=name, event_type=event_type, event_data=event_data
			)
		)

	# [ Reading Events ]
	def on_start(self, device: str):
		pass

	def on_stop(self, device: str):
		pass

	# [ Tag Events ]
	def on_new_tag(self, tag: dict):
		# asyncio.create_task(self.integration.on_tag_integration(tag=tag))
		tag['target'] = self.get_target()
		self.write_target(tag)

	def on_existing_tag(self, tag: dict):
		self.write_target(tag)

	def get_target(self):
		self.serial += 1
		return f'{settings.WRITE_PREFIX}{str(self.serial).zfill(24 - len(settings.WRITE_PREFIX))}'

	def write_target(self, tag: dict):
		tag['write_ok'] = tag.get('epc') == tag.get('target')
		if not tag['write_ok']:
			logging.info(f'[ WRITE ] Writing {tag["target"]} to {tag["epc"]}')
			# Here you would add the actual write command to the RFID device
			write_tag = WriteTagValidator(
				target_identifier='tid',
				target_value=tag.get('tid'),
				new_epc=tag.get('target'),
				password='00000000',
			)
			asyncio.create_task(
				self.devices.write_epc(device_name=tag.get('device'), write_tag=write_tag)
			)

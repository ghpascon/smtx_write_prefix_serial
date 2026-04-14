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
from app.models.rfid import Tag


class Controller:
	def __init__(self, devices: DeviceManager, tags: TagList, integration: Integration):
		self.tags = tags
		self.devices = devices
		self.integration = integration
		self.serial: int = 0

	# [ EVENTS ]
	def on_event(self, name: str, event_type: str, event_data):
		# asyncio.create_task(
		# 	self.integration.on_event_integration(
		# 		name=name, event_type=event_type, event_data=event_data
		# 	)
		# )
		pass

	# [ Reading Events ]
	def on_start(self, device: str):
		pass

	def on_stop(self, device: str):
		pass

	# [ Tag Events ]
	def on_new_tag(self, tag: dict):
		# asyncio.create_task(self.integration.on_tag_integration(tag=tag))
		tag['target'] = self.get_target()
		tag['write_ok'] = False
		tag['last_ok'] = False
		self.save_new_tag(tag)
		self.write_target(tag)

	def on_existing_tag(self, tag: dict):
		self.write_target(tag)

	def get_target(self):
		self.serial += 1
		return f'{settings.WRITE_PREFIX}{str(self.serial).zfill(24 - len(settings.WRITE_PREFIX))}'

	def write_target(self, tag: dict):
		tag['write_ok'] = tag.get('epc') == tag.get('target')

		if tag['last_ok'] != tag['write_ok'] and tag['write_ok']:
			tag['last_ok'] = tag['write_ok']
			self.update_write_ok(tag)

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

	def save_new_tag(self, tag: dict):
		# Se já existir uma tag com o mesmo tid, atualiza os valores; senão, cria nova
		with self.integration.db_manager.get_session() as session:
			db_tag = session.query(Tag).filter_by(tid=tag.get('tid')).first()
			if db_tag:
				db_tag.device = tag.get('device')
				db_tag.epc = tag.get('epc')
				db_tag.ant = tag.get('ant')
				db_tag.rssi = tag.get('rssi')
				db_tag.target = tag.get('target')
				db_tag.write_ok = tag.get('write_ok')
			else:
				new_tag = Tag(
					device=tag.get('device'),
					epc=tag.get('epc'),
					tid=tag.get('tid'),
					ant=tag.get('ant'),
					rssi=tag.get('rssi'),
					target=tag.get('target'),
					write_ok=tag.get('write_ok'),
				)
				session.add(new_tag)

	def update_write_ok(self, tag: dict):
		with self.integration.db_manager.get_session() as session:
			db_tag = session.query(Tag).filter_by(tid=tag.get('tid')).first()
			if db_tag:
				db_tag.write_ok = tag.get('write_ok')
				db_tag.epc = tag.get('epc')

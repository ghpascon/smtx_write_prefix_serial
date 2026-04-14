from fastapi import APIRouter
from fastapi.responses import JSONResponse
from smartx_rfid.utils.path import get_prefix_from_path

from app.services import rfid_manager
from app.core import settings

from smartx_rfid.utils.regex import regex_hex

router_prefix = get_prefix_from_path(__file__)
router = APIRouter(prefix=router_prefix, tags=[router_prefix])


@router.get(
	'/controller_info',
	summary='Get RFID info',
)
async def controller_info():
	controller = rfid_manager.controller

	# Monta dict nome: tipo para atributos e métodos públicos
	info = {}
	for name in dir(controller):
		if name.startswith('_'):
			continue
		attr = getattr(controller, name)
		if callable(attr):
			info[name] = f'function ({type(attr).__name__})'
		else:
			info[name] = type(attr).__name__
	return info


@router.get(
	'/get_write_prefix',
	summary='Get the current write prefix',
)
async def get_write_prefix():
	return {'write_prefix': settings.WRITE_PREFIX}


@router.post(
	'/set_write_prefix/{new_prefix}',
	summary='Set a new write prefix',
)
async def set_write_prefix(new_prefix: str):
	if not regex_hex(new_prefix, len(new_prefix)):
		return JSONResponse(
			status_code=400,
			content={'message': 'Invalid prefix format. Must be a hexadecimal string.'},
		)
	settings.WRITE_PREFIX = new_prefix
	settings.save()
	return {'message': f'Write prefix updated to: {settings.WRITE_PREFIX}'}


@router.get(
	'/get_current_serial',
	summary='Get the current serial number being written to tags',
)
async def get_current_serial():
	current_serial = rfid_manager.controller.serial
	return {'current_serial': current_serial}


@router.post(
	'/set_current_serial/{new_serial}',
	summary='Set a new current serial number',
)
async def set_current_serial(new_serial: int):
	if new_serial < 0:
		return JSONResponse(
			status_code=400,
			content={'message': 'Serial number must be a non-negative integer.'},
		)
	rfid_manager.controller.serial = new_serial
	return {'message': f'Current serial number updated to: {rfid_manager.controller.serial}'}

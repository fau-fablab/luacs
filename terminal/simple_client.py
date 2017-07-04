#!/usr/bin/env python3
import argparse
from pprint import pprint
import logging
from datetime import timedelta, datetime
import threading
import re
import sys

import requests


def timedelta_from_str(s):
    '''Parses timedelta.__str___ back to timedelta objects'''
    p = re.compile(r'(?:(?P<days>\d+) day[s]?, )?'
                   r'(?P<hours>\d{1,2}):(?P<minutes>\d{2}):(?P<seconds>\d{2})')
    m = re.match(p, s)
    if m:
        d = m.groupdict()
        days = int(d['days']) if d['days'] else 0
        h = int(d['hours'])
        m = int(d['minutes'])
        s = int(d['seconds'])
        return timedelta(days=days, seconds=h*3600 + m*60 + s)
    else:
        return None


class TerminalBackendInterface:
    '''Interface from terminal to backend server'''
    def __init__(self, token, base_url):
        self.token = token
        self.base_url = base_url
        self._auth_header = {'Authorization': 'Token '+self.token}
        # Information to be retrieved from backend
        self._info = self.api_get('/terminals/myself')

    def api_get(self, api_path):
        '''
        Requests and returns a json object
        
        api_path may be a full URL or an absolut path bellow base_url.
        '''
        # TODO add support for caching incase a timeout / network error is seen
        
        url = api_path if self.base_url in api_path else self.base_url+api_path
        r = requests.get(url, headers=self._auth_header)
        return r.json()

    def identify_user(self, id_type, id_str):
        '''Returns user that machtes id_type and id_str'''
        # TODO FIXME use api filtering features
        user = [p for p in self.api_get('/profiles/')['results']
                if p['id_type'] == id_type and p['id_string'] == id_str]
        if user:
            return user[0]
        else:
            return None

    def check_permission(self, user_id, dev_shortname):
        '''Returns permission that authorizes user to use device'''
        # TODO FIXME use api filtering features
        dev = self.api_get('/devices/'+dev_shortname)
        perm = [p for p in self.api_get('/permissions/')['results']
                if p['granted_to_id'] == user_id and 
                p['permission_group'] == dev['required_permission_group']]
        if perm:
            return perm[0]
        else:
            return None

    def api_devicestatus_change(self, shortname, in_operation, authorization,
                                reason=None, start_time=None):
        '''Adds new device status'''
        data = {'in_operation': in_operation,
                'authorization': authorization}
        if start_time:
            data['start_time'] = start_time
        if reason:
            data['reason'] = reason
        url = self.base_url+'/device/'+shortname+'/status'
        request.put(url, data=data, header=self._auth_header)

    def get_devices(self):
        '''Creates and returns all devices configured on this terminal'''
        devices = []
        for dev_url in self._info['devices']:
            # TODO add informtion on device class and configuration to backend Device model
            dev_info = self.api_get(dev_url)
            dev = DeviceInterfaceDummy(**dev_info)
            devices.append(dev)
        return devices


class DeviceInterface:
    '''Prototype Device Interface'''
    def __init__(self, shortname, allow_logout_during_operation, automatic_logout,
                 authorization=None, in_operation=False, **kwargs):
        '''Typically instanciated with the backend json data'''
        self.shortname = shortname
        self.allow_logout_during_operation = allow_logout_during_operation
        if type(automatic_logout) is str:
            self.automatic_logout = timedelta_from_str(automatic_logout)
        elif type(automatic_logout) is int:
            self.automatic_logout = timedelta(seconds=automatic_logout)
        else:
            self.automatic_logout = automatic_logout
        self.in_operation = in_operation
        self.authorization = authorization
        self._logout_timer = None
        self.next_timeout = None
        if authorization:
            self.login(authorization)
    
    def reset_logout_timer(self, no_lock=False):
        '''
        Resets logout timer and -if appropriate- starts couting
        
        To be called when device state (in_operation, authorization) changes and at user
        interactions
        '''
        if self._logout_timer:
            # Cancle still running timer
            self._logout_timer.cancel()
        self._logout_timer = None
        self.next_timeout = None
        
        # If no_lock was set (only used at login) and automatic_logout would imediately logout user 
        # (set to zero seconds)
        if no_lock and not self.automatic_logout: return
        
        # If a user is logged in (authorized) and either logout is always allowed 
        if self.authorization and (self.allow_logout_during_operation or not self.in_operation):
            # Setup and start timer
            self._logout_timer = threading.Timer(
                self.automatic_logout.total_seconds(), self.logout, kwargs={'reason': 'timeout'})
            self._logout_timer.start()
            # Set target time
            self.next_timeout = datetime.now() + self.automatic_logout

    def login(self, permission):
        '''Grants access based on the given permission'''
        self.set_lock(False)
        self.authorization = permission
        self.reset_logout_timer(no_lock=True)
        # TODO how to communicate back? callback function?

    def logout(self, reason=None):
        '''Revokes the currently active permission and locks device'''
        if not self.allow_logout_during_operation and self.in_operation:
            raise Exception('Logout may not occure during operation')
        self.set_lock(True)
        self.authorization = None
        self.reset_logout_timer()
        # TODO communicate to backend. callback function?

    def set_operated(self, in_operation, reason=None):
        '''Records operation state change. To be called when device state changes.'''
        if self.in_operation != in_operation:
            self.in_operation = in_operation
            self.reset_logout_timer()
            # TODO communicate to backend. callback function?

    def set_lock(self, state):
        '''
        Sets device's lock state. True = locked, False = unlocked
        
        No service interruption may take place if unlock is set while device was already unlocked
        '''
        raise NotImplemented()

    def __repr__(self):
        return "<{} authorization={} in_operation={} next_timeout={}>".format(
            self.__class__.__name__, self.authorization, self.in_operation, self.next_timeout)


class DeviceInterfaceDummy(DeviceInterface):
    def set_lock(self, state):
        print("{} lock set to {}".format(self.shortname, state))


def interactive(backend):
    '''Interactive CLI Terminal User Interface'''
    devices = backend.get_devices()
    cur_perm = None
    cur_dev = None
    while True:
        # 1. Choose device (if multiple)
        if not cur_dev:
            if len(devices) == 0:
                print('No devices configured. Nothing to do.')
                break
            print('Select device ({}): '.format(' '.join([d.shortname for d in devices])),
                  end='', flush=True)
            if len(devices) == 1:
                # Auto select if only one device is configured
                shortname = devices[0].shortname
                print(shortname)
            else:
                shortname = sys.stdin.readline().strip()
            for d in devices:
                if d.shortname == shortname:
                    cur_dev = d
                    # get permission from device (there might be somebody logged in)
                    cur_perm = cur_dev.authorization
        # 2. Identify and authortize user
        if not cur_perm:
            print('Identifcation <id_type> <id_str>: ', end='', flush=True)
            try:
                id_type, id_str = sys.stdin.readline().strip().split()
            except ValueError as e:
                print('! wrong format', e)
                continue
            cur_user = backend.identify_user(id_type, id_str)
            if not cur_user:
                print("! could not identify user.")
                # TODO Register new user here
                continue
            # Check permission
            cur_perm = backend.check_permission(cur_user['id'], cur_dev.shortname)
            if not cur_perm:
                cur_user = None
                print("! no valid permission found")
                continue
        
        # Login to device
        cur_dev.login(cur_perm)
    
        # Device shell
        print('Commands are: op, nop, change id, change dev, logout, grant <id_type> <id_str>')
        while True:
            print('{} on {}> '.format(cur_perm['granted_to_id'], cur_dev.shortname), end='', flush=True)
            cmd = sys.stdin.readline().strip()
            if cmd == 'help':
                print('Commands are: op, nop, change id, change device, logout, '
                      'grant <id_type> <id_str>')
            elif cmd == 'op':
                cur_dev.set_operated(True)
            elif cmd == 'nop':
                cur_dev.set_operated(False)
            elif cmd == 'change id':
                cur_perm = None
                break
            elif cmd == 'change device':
                cur_dev = None
                cur_perm = None
                break
            elif cmd == 'logout':
                if not cur_dev.allow_logout_during_operation and cur_dev.in_operation:
                    print("! logout may not occure during operation")
                    continue
                cur_dev.logout()
                cur_dev = None
                cur_perm = None
                break
            elif cmd.startswith('grant '):
                try:
                    id_type, id_str = cmd.split()[1:]
                except ValueError as e:
                    print("! wrong format", e)
                    continue
                print('? not yet implemented')
                # TODO grant permission
            else:
                print("! command not understood")

def main():
    parser = argparse.ArgumentParser(description='Example implementation of a LUACS terminal.')
    parser.add_argument('token', metavar='TOKEN', type=str,
                        help='API authentication token of terminal')
    parser.add_argument('--url', type=str, default='http://localhost:8000/luacs/api',
                        help='Backend server API base URL (default: '
                             'http://localhost:8000/luacs/api)')
    args = parser.parse_args()
    
    backend = TerminalBackendInterface(args.token, args.url)
    
    try:
        interactive(backend)
    except KeyboardInterrupt:
        print()

if __name__ == '__main__':
    main()

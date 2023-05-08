import os
import urllib3
import requests
from datetime import datetime
from configparser import ConfigParser
from requests.cookies import RequestsCookieJar

##
## Omada API calls expect a timestamp in milliseconds.
##
def timestamp():
	return int( datetime.utcnow().timestamp() * 1000 )

##
## Display errorCode and optional message returned from Omada API.
##
class OmadaError(Exception):

	def __init__(self, json):
		self.errorCode = 0
		self.msg = None

		if 'errorCode' in json:
			self.errorCode = int( json['errorCode'] )

		if 'msg' in json:
			self.msg = '"' + json['msg'] + '"'

	def __str__(self):
		return f'errorCode={self.errorCode}, msg={self.msg}'


class Omada:
	API_PATH = '/api/v2'
	CONFIG_PATH = 'omada_config.cfg'
    
	def __init__(self):
		self.config = ConfigParser()
		self.loginResult = None
		self.currentPageSize = 10
		self.currentUser = {}

		if os.path.isfile(self.CONFIG_PATH) is not True:
			raise TypeError('omada_config.cfg is missing')

		try:
			self.config.read(self.CONFIG_PATH)
			print(self.config['omada'])
			self.baseurl  = self.config['omada'].get('baseurl')
			self.omadacId  = self.config['omada'].get('omadacId')
			self.site     = self.config['omada'].get('site', 'Default')
			self.verify   = self.config['omada'].getboolean('verify', True)
			self.warnings = self.config['omada'].getboolean('warnings', True)
			self.verbose  = self.config['omada'].getboolean('verbose', False)
		except Exception as e:
			raise

		# set up requests session and cookies
		self.session = requests.Session()
		self.session.cookies = RequestsCookieJar()
		self.session.verify = self.verify

		# hide warnings about insecure SSL requests
		if self.verify == False and self.warnings == False:
			urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

	##
	## Build request URL for the provided path
	##
	def __buildUrl(self, path):
		return self.baseurl + self.omadacId + self.API_PATH + path
	
	##
	## Get OmadacId to prefix request. (Required for version 5.)
	##
	def getApiInfo(self):
		# This uses a different path, so perform request manually.
		if self.omadacId is not None:
			url = self.baseurl + self.omadacId
		else:
			url = self.baseurl

		response = self.session.get( url + '/api/info' )
		response.raise_for_status()

		json = response.json()
		if json['errorCode'] == 0:
			return json['result'] if 'result' in json else None
		
		raise
	
	##
	## Log in with the provided credentials and return the result.
	##
	def login(self, asAdmin = False):

		# Only try to log in if we're not already logged in.
		if self.loginResult is None:

			# Fetch omadacId
			if self.omadacId is None:
				apiInfo = self.getApiInfo()
				if 'omadacId' in apiInfo:
					self.omadacId = apiInfo['omadacId']
				else:
					raise TypeError('Unable to fetch omadacId.')

			try:
				if asAdmin is True:
					username_key = 'username'
					password_key = 'password'
				else:
					username_key = 'operator_username'
					password_key = 'operator_password'
				username = self.config['omada'].get(username_key)
				password = self.config['omada'].get(password_key)
			except:
				raise

			json_request = {'password': password}
			if asAdmin is True:
				url_path = '/login'
				json_request['username'] = username
			else:
				url_path = '/hotspot/login'
				json_request['name'] = username

			# Perform the login request manually.
			response = self.session.post( self.__buildUrl(url_path), json=json_request)
			response.raise_for_status()

			# Get the login response.
			json = response.json()

			# Raise an error if logged in failed
			if json['errorCode'] != 0:
				raise OmadaError(json)

			# Store the login result.
			self.loginResult = json['result']

			# Store CSRF token header.
			self.session.headers.update({
				"Csrf-Token": self.loginResult['token']
			})

			# Get the current user info.
			self.currentUser = self.getCurrentUser(asAdmin=asAdmin)

		return self.loginResult
	
	##
	## Returns the current user information.
	##
	def getCurrentUser(self, asAdmin = False):
		if asAdmin is True:
			return self.__get( '/users/current' )
		else:
			return self.__get( '/hotspot/current' )
	
	##
	## Log out of the current session. Return value is always None.
	##
	def logout(self):

		result = None

		# Only try to log out if we're already logged in.
		if self.loginResult is not None:
			# Send the logout request.
			result = self.__post( '/hotspot/logout' )
			# Clear the stored result.
			self.loginResult = None

		return result
	
	##
	## Look up a site key given the name.
	##
	def __findSiteId(self, name=None):
		# Use the stored site if not provided.
		if name is None: name = self.site

		# Look for the site in the privilege list.
		if 'privilege' in self.currentUser:
			for site in self.currentUser['privilege']['sites']:
				if site['name'] == name:
					return site['key']
		else:
			for site in self.currentUser['sites']:
				if site['name'] == name:
					return site['key']

		raise PermissionError(f'current user does not have privilege to site "{name}"')
	
	##
	## Perform a GET request and return the result.
	##
	def __get(self, path, params={}, data=None, json=None):

		if self.loginResult is None:
			raise ConnectionError('Not logged in.')

		if not isinstance(params, dict):
			raise TypeError('params must be a dictionary')

		response = self.session.get( self.__buildUrl(path), params=params, data=data, json=json, headers=self.session.headers )
		response.raise_for_status()

		json = response.json()
		if json['errorCode'] == 0:
			return json['result'] if 'result' in json else None
		
		raise OmadaError(json)
		
	##
	## Perform a POST request and return the result.
	##
	def __post(self, path, params={}, data=None, json=None):

		if self.loginResult is None:
			raise ConnectionError('not logged in')

		if not isinstance(params, dict):
			raise TypeError('params must be a dictionary')

		params['_'] = timestamp()
		params['token'] = self.loginResult['token']

		response = self.session.post( self.__buildUrl(path), params=params, data=data, json=json )
		response.raise_for_status()

		json = response.json()
		if json['errorCode'] == 0:
			return json['result'] if 'result' in json else None

		raise OmadaError(json)
	
	##
	## Return True if a result contains data.
	##
	def __hasData(self, result):
		return (result is not None) and ('data' in result) and (len(result['data']) > 0)

	##
	## Perform a paged GET request and return the result.
	##
	def __getPaged(self, path, params={}, data=None, json=None):

		if self.loginResult is None:
			raise ConnectionError('not logged in')

		if not isinstance(params, dict):
			raise TypeError('params must be a dictionary')

		params['_'] = timestamp()
		params['token'] = self.loginResult['token']

		if 'currentPage' not in params:
			params['currentPage'] = 1

		if 'currentPageSize' not in params:
			params['currentPageSize'] = self.currentPageSize

		response = self.session.get( self.__buildUrl(path), params=params, data=data, json=json )
		response.raise_for_status()

		json = response.json()
		if json['errorCode'] == 0:
			json['result']['path'] = path
			json['result']['params'] = params
			return json['result']

		raise OmadaError(json)

	##
	## Returns the next page of data if more is available.
	##
	def __nextPage(self, result):

		if 'path' in result:
			path = result['path']
			del result['path']
		else:
			return None

		if 'params' in result:
			params = result['params']
			del result['params']
		else:
			return None

		totalRows   = int( result['totalRows'] )
		currentPage = int( result['currentPage'] )
		currentSize = int( result['currentSize'] )
		dataLength  = len( result['data'] )

		if dataLength + (currentPage-1)*currentSize >= totalRows:
			return None

		params['currentPage'] = currentPage + 1
		return self.__getPaged( path, params )

	##
	## Perform a GET request and yield the results.
	##
	def __geterator(self, path, params={}, data=None, json=None):
		result = self.__getPaged( path, params, data, json )
		while self.__hasData( result ):
			for item in result['data']: yield item
			result = self.__nextPage( result )
	
	##
	## Perform a DELETE request and return the result.
	##
	def __delete(self, path, params={}, data=None, json=None):

		if self.loginResult is None:
			raise ConnectionError('not logged in')

		if not isinstance(params, dict):
			raise TypeError('params must be a dictionary')

		response = self.session.delete( self.__buildUrl(path), params=params, data=data, json=json, headers=self.session.headers )
		response.raise_for_status()

		json = response.json()
		if json['errorCode'] == 0:
			return json['result'] if 'result' in json else None

		raise OmadaError(json)
	
	##
	## Get All Hotspot Portals
	##
	def getAllPortals(self):
		return self.__get( f'/hotspot/sites/setting/voucher/portals' )
	
	##
	## Get Rate Limit Profiles
	##
	def getRateLimitProfiles(self, site=None):
		return self.__get( f'/hotspot/sites/{self.__findSiteId(site)}/setting/profiles/rateLimits' )
	
	##
	## Disconnect user
	##
	def disconnectClient(self, id=None, mac=None, site=None):
		if id is not None:
			return self.__post( f'/hotspot/sites/{self.__findSiteId(site)}/cmd/clients/{id}/disconnect')
		elif mac is not None:
			return self.__post( f'/sites/{self.__findSiteId(site)}/cmd/clients/{mac}/unauth')
	
	##
	## Create a Voucher
	##
	def createVoucher(self, json, site=None):
		return self.__post( f'/hotspot/sites/{self.__findSiteId(site)}/vouchers', json = json)
	
	##
	## Get All Vouchers
	##
	def getAllVouchers(self, site=None):
		return self.__geterator( f'/hotspot/sites/{self.__findSiteId(site)}/vouchers?sorts.valid=desc', params={})

	##
	## Get Voucher base on note
	##
	def getVoucher(self, voucherNote, site=None):
		return self.__get( f'/hotspot/sites/{self.__findSiteId(site)}/vouchers?searchKey={voucherNote}' )
	
	##
	## Delete a Voucher
	##
	def deleteVoucher(self, id, site=None):
		return self.__delete( f'/hotspot/sites/{self.__findSiteId(site)}/vouchers/{id}')
	
	##
	## Returns the list of active clients for given site.
	##
	def getAllActiveClients(self, site=None):
		return self.__geterator( f'/sites/{self.__findSiteId(site)}/clients', params={'filters.active':'true'})
	
	##
	## Get All Authed Clients for the last 5 days (in milliseconds)
	##
	def getAllAuthedClients(self, site=None):
		return self.__geterator( f'/hotspot/sites/{self.__findSiteId(site)}/clients?sorts.valid=desc', params={'filters.timeStart': timestamp() - 432000000})
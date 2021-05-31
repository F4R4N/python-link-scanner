#!/bin/python3
import requests
from bs4 import BeautifulSoup
import re
import time
import json

SUCCESS = "\033[92m[ CHECKED ]\033[0m | "  # label URL as CHECKED
FAIL = "\033[91m*[ BROKEN ]\033[0m | "  # label URL as BROKEN
WARNING = "\033[93m+[ HTTP ]\033[0m | "  # label URL as HTTP

class UrlHandler:
	def __init__(self, root_url_or_path, main_domain=None, save_in_file=False, filename=None):
		self.root_url_or_path = root_url_or_path
		self.main_domain = main_domain
		self.save_in_file = save_in_file
		self.filename = filename
		self.broken_filename = None
		self.load_from_url = self.url_load_source()
		self.all_urls = []
		self.all_urls_status = []
		self.all_broken_urls = []
		self.all_http_urls = []
		# necessary methods call by default
		self.set_main_domain()
		self.extract_urls()

	def url_load_source(self):
		""" set load from URL to True if user input is URL """
		if re.match(r"^https:\/\/.*|^http:\/\/.*", self.root_url_or_path):
			return True
		return False

	def get_main_domain(self):
		""" extract main domain from URL in user input """
		if self.root_url_or_path[-1] != "/":
			self.root_url_or_path += "/"
		return re.match(r"^https:\/\/.*?\/", self.root_url_or_path).group()[:-1]

	def set_main_domain(self):
		""" set main domain value based on get main domain output """
		if not self.load_from_url and self.main_domain is None:
			domain = input("enter the URL's main domain if there is a relative URL in file(if there is not leave it blank):")
			if domain == "":
				self.main_domain = None
			elif re.match(r"^http:\/\/|^https:\/\/", domain) is None:
				print("ERROR: please enter a valid URL")
				exit()
		if self.load_from_url:
			self.main_domain = self.get_main_domain()

	def slugify(self, value):
	    value = "".join(x for x in value if x.isalnum())
	    return value


	def set_filenames(self):
		""" set default filename if user don't provide one """
		if self.filename is None:
			self.filename = self.slugify(self.main_domain)
			print(f"\nset default filename to '{self.filename}.json' since no filename associated.")

	def save_urls_in_file(self, urls):
		self.set_filenames()
		with open(self.filename+".json", "w") as file:
			for url in urls:
				json_data = json.dumps(url)
				file.write(json_data+"\n")

	def extract_urls(self):
		""" extract all URL's from given website URL """
		if self.load_from_url:
			response = requests.get(self.root_url_or_path).text
			soup = BeautifulSoup(response, "html.parser")
			all_a = soup.find_all('a')  # find all 'a' elements in HTML
			for a in all_a:
				if a.get("href"):
					self.all_urls.append(a.get("href"))  # get 'href' property of all 'a' elements(URL's)
		else:
			try:
				with open(self.root_url_or_path, "r") as file:
					grouped_urls = re.findall(r"((http|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?)", file.read())
					for url in grouped_urls:
						self.all_urls.append(url[0])
			except OSError:
				print(f"ERROR: unable to open '{self.root_url_or_path}', make sure it exist and try again.")
				exist()

	def set_urls(self, url_status):
		self.all_urls_status.append(url_status)

	def get_broken_urls(self):
		for url in self.all_urls_status:
			if not url["accessible"]:
				self.all_broken_urls.append(url)
		return self.all_broken_urls

	def get_http_urls(self):
		for url in self.all_urls_status:
			if url["type"] == "http":
				self.all_http_urls.append(url)
		return self.all_http_urls


	def get_all_urls(self):
		return self.all_urls

	def __str__(self):
		return self.root_url_or_path


class Url:
	def __init__(self, url, main_domain=None):
		self.url = url
		self.main_domain = main_domain  # use to convert relative URL's to absolute
		self.type = None  # could be 'http', 'https' or None=> when its sharp_url
		self.status = None  # True is for accessible and False for not None is for sharp_url's

	def clean_url(self):
		""" set URL type and convert it to absolute if its relative URL """
		if re.match(r"^\#.*", self.url):
			self.type = None
		elif re.match(r"^http:\/\/.*", self.url):
			self.type = "http"
		elif re.match(r"^https:\/\/.*", self.url):
			self.type = "https"
		elif re.match(r"^\/.*", self.url):
			self.url = self.main_domain + self.url  # convert relative URL to absolute URL
			self.type = "https"

	def test_url(self):
		""" send request to the URL and set URL status """
		if self.type is not None:
			try:
				response = requests.get(self.url)
				self.status = response.ok
			except requests.exceptions.ConnectionError:
				self.status = False

	def get_status(self):
		""" clean URL and test it then return dictionary of status, url, type """
		self.clean_url()
		self.test_url()
		return {"accessible": self.status, "type": self.type, "url": self.url}

	def __str__(self):
		return self.url

def main():
	try:
		url_or_path = input("enter URL or file path: ")
		save_in_file = input("save result in file?(y or Y to accept any other key to not): ")
		start = time.perf_counter()
		save_in_file = True if save_in_file == "y" or save_in_file == "Y" else False
		url_handler = UrlHandler(url_or_path)
		all_urls = url_handler.get_all_urls()
		all_urls_status = []
		for url in all_urls:
			test = Url(url, url_handler.main_domain).get_status()
			url_handler.set_urls(test)
			all_urls_status.append(test)
			if test["accessible"]:
				print(SUCCESS+test["url"]) if test["type"] == "https" else print(SUCCESS+WARNING+test["url"])
			elif test["accessible"] is False:
				print(FAIL+test["url"]) if test["type"] == "https" else	print(FAIL+WARNING+test["url"])

		if save_in_file:
			url_handler.save_urls_in_file(all_urls_status)
		total_time = time.perf_counter() - start  # measure script running time
		print("+-+-+-+ SUMMARY +-+-+-+")
		print("\n+-+-+-+ Broken URL's +-+-+-+")
		for broken_url_status in url_handler.get_broken_urls():
			print(FAIL+broken_url_status["url"])
		print("\n+-+-+-+ HTTP URL's +-+-+-+")
		for http_url_status in url_handler.get_http_urls():
			print(WARNING+http_url_status["url"])
		print(f"\nscanned URL's from '{url_or_path}'")
		print(f"it took total '{total_time:5.2f}' second to scan URL's.")  # allow only 2 float number
		print(f"scanned total '{len(all_urls_status)}' URL's.")
	except KeyboardInterrupt:  # stop script to throw track-back on Ctrl+C
		print("closing the program...")
		exit()

if __name__ == '__main__':
	main()

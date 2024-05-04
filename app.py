from flask import Flask, render_template, request
from scraper import jobstreet_scraper, kalibrr_scraper, karir_scraper, linkedin_scraper
import requests

app = Flask(__name__)
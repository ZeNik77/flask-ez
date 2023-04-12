from flask import Flask, render_template, request, redirect
from routes import app
import subprocess


app.run(debug = True, port=5000)
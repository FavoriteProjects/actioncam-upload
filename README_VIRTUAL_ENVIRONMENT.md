Virtual environment setup
=========================

Create the account:
-------------------
$ mkdir -p ~/.python-virtual-environment/actioncam-upload
$ python3 -m venv ~/.python-virtual-environment/actioncam-upload
$ pip install --upgrade pip setuptools google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

Activate the virtual environment:
---------------------------------
$ source ~/.python-virtual-environment/actioncam-upload/bin/activate

When done:
----------
$ deactivate

Normally, this utility will be installed and upgraded by the TARPN installer scripts. 
The following are manual installation instructions.

Determine your desired installation directory
```commandline
export INSTALL_DIR=/opt/tarpn
```

Create a virtualenv 

```commandline
sudo mkdir -p $INSTALL_DIR
sudo chown pi:pi $INSTALL_DIR
python3 -m venv $INSTALL_DIR
```

Install the stress test package
```commandline
$INSTALL_DIR/bin/pip install --upgrade https://github.com/tarpn/tarpn-stress-test/releases/download/v0.1/tarpn_stress_test-0.1-py3-none-any.whl
```

The script can be run directly from its installation directory

```commandline
$INSTALL_DIR/bin/tarpn-stress-test
```

If desired, create a symlink to add to your PATH.
```commandline
sudo ln -s $INSTALL_DIR/bin/tarpn-stress-test /usr/tarpn/sbin/tarpn-stress-test
```
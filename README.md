# Galia

Gesture controlled gallery.

[http://outboxlabs.com/galia](http://outboxlabs.com/galia)

## Get it running

### 1. Install the following:

#### OpenNI, NITE and SensorKinect

Download latest x86 unstable version from:

    http://openni.org/
    https://github.com/avin2/SensorKinect/tree/unstable/Bin  

Unpack each and run: 

    sudo ./install.sh

#### Panda3D

Download and install from: 

    http://www.panda3d.org/download.php?sdk&version=devel

#### Boost

We use boost::python and boost::thread. boost::python must be linked to the same version of Python used by Panda3D (2.5 in OSX). To install in OSX with brew first run:
   brew edit boost

And apply this diff:

    --- a/Library/Formula/boost.rb
    +++ b/Library/Formula/boost.rb
    @@ -65,7 +65,7 @@ class Boost < Formula
         args << "address-model=32_64" << "architecture=x86" << "pch=off" if ARGV.include? "--universal"
     
         # we specify libdir too because the script is apparently broken
    -    system "./bootstrap.sh", "--prefix=#{prefix}", "--libdir=#{lib}"
    +    system "./bootstrap.sh", "--prefix=#{prefix}", "--libdir=#{lib}", "--with-python-version=2.5", "--with-python-root=/System/Library/Frameworks/Python.framework/Versions/2.5"
         system "./bjam", *args
       end
     end

Then run:
  
    brew install boost --universal --build-from-source

#### Cmake

With Homebrew: 

    brew install cmake

### 2. Compile the python extension

    mkdir build
    cd build
    cmake ..
    make

### 3. Configure the app

Change the `image_path` variable in: 

    app/config.py 

and set a resolution in 

    local-config.prc

### 3. Connect Kinect and run:

    ppython main.py

## License

![Creative Commons](http://i.creativecommons.org/l/by-nc-sa/3.0/88x31.png)

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.](http://creativecommons.org/licenses/by-nc-sa/3.0/)
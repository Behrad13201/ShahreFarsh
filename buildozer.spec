
[app]

title = Haghayegh Shahr Farsh
package.name = haghayeghshahrfarsh
package.domain = org.behrad

source.dir = .
source.include_exts = py,png,jpg,jpeg,mp3,kv,atlas
version = 1.0

requirements = python3,kivy==2.3.1

orientation = landscape
fullscreen = 1

android.api = 35
android.minapi = 23
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True

p4a.branch = master

[buildozer]

log_level = 2
warn_on_root = 1

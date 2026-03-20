import re

# ── emg.ui ──────────────────────────────────────────────────────────────────
path_emg = r'ui/experiment/pages/emg.ui'
with open(path_emg, encoding='utf-8') as f:
    txt = f.read()

# 1. verstretch=1 SOLO en frameInstructions sizePolicy (primer <verstretch>0</verstretch>)
txt = txt.replace(
    '<horstretch>0</horstretch>\r\n        <verstretch>0</verstretch>\r\n       </sizepolicy>\r\n      </property>\r\n      <property name=\"frameShape\">',
    '<horstretch>0</horstretch>\r\n        <verstretch>1</verstretch>\r\n       </sizepolicy>\r\n      </property>\r\n      <property name=\"frameShape\">',
    1
)

# 2. scaledContents false en lblEmgImage
txt = txt.replace(
    '<property name=\"scaledContents\">\r\n          <bool>true</bool>\r\n         </property>\r\n         <property name=\"alignment\">\r\n          <set>Qt::AlignmentFlag::AlignCenter</set>',
    '<property name=\"scaledContents\">\r\n          <bool>false</bool>\r\n         </property>\r\n         <property name=\"alignment\">\r\n          <set>Qt::AlignmentFlag::AlignCenter</set>',
    1
)

# 3. stretch=1 en el item que contiene horizontalLayoutBottom
txt = txt.replace(
    '   <item>\r\n     <layout class=\"QHBoxLayout\" name=\"horizontalLayoutBottom\">',
    '   <item stretch=\"1\">\r\n     <layout class=\"QHBoxLayout\" name=\"horizontalLayoutBottom\">',
    1
)

with open(path_emg, 'w', encoding='utf-8') as f:
    f.write(txt)

print('emg.ui OK')

# ── login.ui ─────────────────────────────────────────────────────────────────
path_login = r'ui/login/login.ui'
with open(path_login, encoding='utf-8') as f:
    txt = f.read()

# 4. Añadir alignment AlignHCenter al verticalLayoutLeft
txt = txt.replace(
    '      <layout class=\"QVBoxLayout\" name=\"verticalLayoutLeft\">\r\n       <item>\r\n        <spacer name=\"verticalSpacerLeftTop\">',
    '      <layout class=\"QVBoxLayout\" name=\"verticalLayoutLeft\">\r\n       <property name=\"alignment\">\r\n        <set>Qt::AlignmentFlag::AlignHCenter</set>\r\n       </property>\r\n       <item>\r\n        <spacer name=\"verticalSpacerLeftTop\">',
    1
)

# 5. sizePolicy Fixed en labelEUSab
txt = txt.replace(
    '         <property name=\"sizePolicy\">\r\n          <sizepolicy hsizetype=\"Preferred\" vsizetype=\"Preferred\">\r\n           <horstretch>0</horstretch>\r\n           <verstretch>0</verstretch>\r\n          </sizepolicy>\r\n         </property>\r\n         <property name=\"maximumSize\">\r\n          <size>\r\n           <width>351</width>',
    '         <property name=\"sizePolicy\">\r\n          <sizepolicy hsizetype=\"Fixed\" vsizetype=\"Preferred\">\r\n           <horstretch>0</horstretch>\r\n           <verstretch>0</verstretch>\r\n          </sizepolicy>\r\n         </property>\r\n         <property name=\"maximumSize\">\r\n          <size>\r\n           <width>351</width>',
    1
)

with open(path_login, 'w', encoding='utf-8') as f:
    f.write(txt)

print('login.ui OK')


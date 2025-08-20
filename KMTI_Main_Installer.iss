[Dirs]
Name: "{app}\data\sessions"
; -- Inno Setup Script for KMTI Main Application (Rebuilt) --
; Bundles PyInstaller output from dist/, assets/, and data/ (logs, sessions, config.json)

[Setup]
AppName=KMTI File Management System
AppVersion=1.0
DefaultDirName={pf}\kmti-main
DefaultGroupName=KMTI
OutputDir=dist
OutputBaseFilename=KMTIFMS-setup
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
SetupIconFile=assets\\fms-icon.ico

[Files]
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "data\logs\*"; DestDir: "{app}\data\logs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "data\config.json"; DestDir: "{app}\data"; Flags: ignoreversion

[Icons]
Name: "{group}\KMTI File Management System"; Filename: "{app}\main.exe"; IconFilename: "{app}\assets\fms-icon.ico"
Name: "{userdesktop}\KMTI File Management System"; Filename: "{app}\KMTI File Management System.exe"; IconFilename: "{app}\assets\fms-icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\main.exe"; Description: "Launch KMTI File Management System"; Flags: nowait postinstall skipifsilent

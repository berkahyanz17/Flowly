[Setup]
AppName=Flowly
AppVersion=1.1
DefaultDirName={autopf}\Flowly
DefaultGroupName=Flowly
OutputDir=installer_output
OutputBaseFilename=FlowlySetup
Compression=lzma
SolidCompression=yes
SetupIconFile=installer_assets\icon.ico

[Files]
Source: "dist\Flowly.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_assets\flowly.db"; DestDir: "{userappdata}\Flowly"; Flags: onlyifdoesntexist

[Dirs]
Name: "{userappdata}\Flowly"

[Icons]
Name: "{group}\Flowly"; Filename: "{app}\Flowly.exe"
Name: "{commondesktop}\Flowly"; Filename: "{app}\Flowly.exe"

[Run]
Filename: "{app}\Flowly.exe"; Description: "Launch Flowly"; Flags: nowait postinstall skipifsilent

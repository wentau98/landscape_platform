[Setup]
AppName=园林景观方案智能设计平台
AppVersion=1.0
DefaultDirName={autopf}\LandscapePlatform
DefaultGroupName=园林景观方案智能设计平台
OutputDir=Output
OutputBaseFilename=LandscapePlatform_Setup_v1.0
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 将 PyInstaller 生成的 dist 文件夹下的所有内容打包
Source: "dist\园林景观智能设计平台\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\园林景观方案智能设计平台"; Filename: "{app}\园林景观智能设计平台.exe"
Name: "{autodesktop}\园林景观方案智能设计平台"; Filename: "{app}\园林景观智能设计平台.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\园林景观智能设计平台.exe"; Description: "立即启动平台"; Flags: nowait postinstall skipifsilent
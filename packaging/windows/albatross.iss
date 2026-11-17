; Inno Setup script for the Albatross Windows installer.
; The CI passes MyAppVersion, RepoRoot, SourceExe and OutputDir with /D.

#ifndef MyAppVersion
  #define MyAppVersion "0.1.0"
#endif
#ifndef RepoRoot
  #define RepoRoot "."
#endif
#ifndef SourceExe
  #define SourceExe "dist/Albatross-windows.exe"
#endif
#ifndef OutputDir
  #define OutputDir "dist/installers"
#endif

[Setup]
AppId={{8AD1E22A-480B-4696-9378-F8F0B82231A2}
AppName=Albatross
AppVersion={#MyAppVersion}
AppVerName=Albatross {#MyAppVersion}
AppPublisher=Pavlenko Evgeniy
AppPublisherURL=https://github.com/PavlenkoEvgeniy/python-game-albatros
AppSupportURL=https://github.com/PavlenkoEvgeniy/python-game-albatros/issues
AppUpdatesURL=https://github.com/PavlenkoEvgeniy/python-game-albatros/releases
DefaultDirName={autopf}\Albatross
DefaultGroupName=Albatross
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=Albatross-{#MyAppVersion}-windows-setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile={#RepoRoot}/packaging/icons/albatross.ico
UninstallDisplayIcon={app}\Albatross.exe
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceExe}"; DestDir: "{app}"; DestName: "Albatross.exe"; Flags: ignoreversion

[Icons]
Name: "{group}\Albatross"; Filename: "{app}\Albatross.exe"
Name: "{autodesktop}\Albatross"; Filename: "{app}\Albatross.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Albatross.exe"; Description: "{cm:LaunchProgram,Albatross}"; Flags: nowait postinstall skipifsilent

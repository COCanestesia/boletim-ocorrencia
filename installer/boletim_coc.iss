#define MyAppName "Boletim de Ocorrência COC"
#define MyAppPublisher "COC Anestesia"
#define MyAppExeName "COCBoletim.exe"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif

[Setup]
AppId={{B36D89BF-7F0B-4D9A-BAE8-4323890D0A54}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\COC\BoletimOcorrencia
DefaultGroupName=COC
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist-installer
OutputBaseFilename=Instalar_Boletim_COC_{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupLogging=yes
CloseApplications=yes
RestartApplications=no
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\COCBoletim\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autodesktop}\Boletim de Ocorrência COC"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{userprograms}\COC\Boletim de Ocorrência COC"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Boletim de Ocorrência COC"; Flags: nowait postinstall skipifsilent

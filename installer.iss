#ifndef MyAppVersion
  #define MyAppVersion "0.3.0"
#endif

#ifndef OutputBaseFilename
  #define OutputBaseFilename "GerenciadorDeArmazenamento-Setup"
#endif

[Setup]
AppId={{A55BC48A-CB7C-4CF5-A8C2-2BC5C379F61E}
AppName=Gerenciador de Armazenamento
AppVersion={#MyAppVersion}
AppPublisher=Fuper
DefaultDirName={localappdata}\Programs\GerenciadorDeArmazenamento
DefaultGroupName=Gerenciador de Armazenamento
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile=assets\app_icon.ico
UninstallDisplayIcon={app}\GerenciadorDeArmazenamento.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos:"

[Files]
Source: "dist\GerenciadorDeArmazenamento.exe"; DestDir: "{app}"; Flags: ignoreversion
#ifdef IncludeSecret
Source: "client_secret.json"; DestDir: "{app}"; Flags: ignoreversion onlyifdoesntexist
#endif

[Icons]
Name: "{group}\Gerenciador de Armazenamento"; Filename: "{app}\GerenciadorDeArmazenamento.exe"
Name: "{autodesktop}\Gerenciador de Armazenamento"; Filename: "{app}\GerenciadorDeArmazenamento.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\GerenciadorDeArmazenamento.exe"; Description: "Abrir o Gerenciador de Armazenamento"; Flags: nowait postinstall skipifsilent

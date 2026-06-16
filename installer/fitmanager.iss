; ══════════════════════════════════════════════════════════════
; FitManager AI Studio — Inno Setup Script
; ══════════════════════════════════════════════════════════════
;
; Produce: FitManager_Setup_1.0.5.exe (~100 MB)
; Requisiti: Inno Setup 6+ (winget install JRSoftware.InnoSetup)
;
; Compilazione:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\fitmanager.iss
;
; Struttura installazione:
;   {app}\
;     launcher.bat
;     backend\       (PyInstaller output)
;     frontend\      (Next.js standalone)
;     node\          (node.exe runtime ~40MB)
;     data\          (creata al primo avvio, preservata sugli aggiornamenti)

#define MyAppName "FitManager AI Studio"
; Versione iniettata da build-installer.sh via /DMyAppVersion=X.Y.Z (SSoT: api/__init__.py)
; Il #define sotto serve come fallback per compilazione manuale diretta.
#ifndef MyAppVersion
  #define MyAppVersion "1.0.12"
#endif

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=FitManager
AppPublisherURL=https://fitmanagerstudio.com
DefaultDirName={autopf}\FitManager
DefaultGroupName=FitManager
OutputBaseFilename=FitManager_Setup_{#MyAppVersion}
OutputDir=..\dist
Compression=lzma2/ultra
SolidCompression=yes
; Icona personalizzata (placeholder — sostituire con icona reale)
; SetupIconFile=assets\fitmanager.ico
LicenseFile=assets\EULA.txt
PrivilegesRequired=lowest
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayName={#MyAppName}
; Aggiornamento "a caldo": Restart Manager rileva i processi che bloccano i file
; in fase di sovrascrittura (es. node.exe sul frontend) e li chiude — scoping per
; lock di file, nessun danno a processi node.exe estranei. Il kill esplicito dei
; binari app-specifici e' in [Code] PrepareToInstall (copre l'frpc.exe orfano che
; RM puo' non rilevare perche' nipote detached senza finestra).
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "italian"; MessagesFile: "compiler:Languages\Italian.isl"

[Files]
; Backend (PyInstaller output)
Source: "..\dist\fitmanager\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs

; Frontend (Next.js standalone)
Source: "..\frontend\.next\standalone\*"; DestDir: "{app}\frontend"; Flags: ignoreversion recursesubdirs

; Node.js runtime (scaricato separatamente, ~40MB)
; NOTA: node.exe va scaricato da https://nodejs.org e messo in installer\node\
Source: "node\node.exe"; DestDir: "{app}\node"; Flags: ignoreversion

; Launcher
Source: "launcher.bat"; DestDir: "{app}"; Flags: ignoreversion

; Catalog DB (encrypted AES-256-GCM — tassonomia scientifica)
Source: "..\dist\release-data\catalog.db.enc"; DestDir: "{app}\data"; Flags: ignoreversion

; Nutrition DB (encrypted AES-256-GCM — catalogo alimenti CREA/USDA)
Source: "..\dist\release-data\nutrition.db.enc"; DestDir: "{app}\data"; Flags: ignoreversion

; Chiave pubblica licenza (verifica firma JWT RSA)
; Fonte canonica: data/license_public.pem, stageata in dist/release-data per evitare lock sul file live.
Source: "..\dist\release-data\license_public.pem"; DestDir: "{app}\data"; Flags: ignoreversion

; Foto esercizi attivi (staging da build-media.sh, ~36MB)
Source: "..\dist\media\exercises\*"; DestDir: "{app}\data\media\exercises"; Flags: ignoreversion recursesubdirs

; EULA gia' visualizzata via LicenseFile nel setup; non serve installarla come file separato.
; Source: "assets\EULA.txt"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Cartella data preservata sugli aggiornamenti
Name: "{app}\data"; Flags: uninsneveruninstall
Name: "{app}\data\backups"; Flags: uninsneveruninstall
Name: "{app}\data\media"; Flags: uninsneveruninstall
Name: "{app}\data\media\exercises"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\FitManager AI Studio"; Filename: "{app}\launcher.bat"; WorkingDir: "{app}"
Name: "{autodesktop}\FitManager AI Studio"; Filename: "{app}\launcher.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crea icona sul Desktop"; GroupDescription: "Icone aggiuntive:"

[Run]
; Apri l'app dopo l'installazione
Filename: "{app}\launcher.bat"; Description: "Avvia FitManager AI Studio"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Non eliminare data/ durante la disinstallazione (dati utente)
; Elimina solo file di programma
Type: filesandordirs; Name: "{app}\backend"
Type: filesandordirs; Name: "{app}\frontend"
Type: filesandordirs; Name: "{app}\node"
Type: files; Name: "{app}\launcher.bat"

[Code]
procedure KillProcess(const ExeName: String);
var
  ResultCode: Integer;
begin
  // /F = forza, /T = anche l'albero dei figli. Stesso utente -> nessun admin.
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/IM ' + ExeName + ' /F /T', '',
       SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  // Termina i processi FitManager attivi PRIMA di sovrascrivere i binari.
  // Causa storica (codice 5 / Accesso negato su backend\frpc.exe): un frpc.exe
  // orfano da una versione precedente — nipote detached che sopravvive alla
  // chiusura del launcher — tiene il lock sul proprio .exe. Entrambi i nomi sono
  // specifici dell'app, quindi il kill per nome e' sicuro (nessun collaterale).
  KillProcess('frpc.exe');
  KillProcess('fitmanager.exe');
  Result := '';
end;

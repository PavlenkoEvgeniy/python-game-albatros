Name:           albatross
Version:        @VERSION@
Release:        1
Summary:        A calm arcade game about an albatross gliding from a mountain
License:        MIT
URL:            https://github.com/PavlenkoEvgeniy/python-game-albatros
BuildArch:      %{_arch}

# The PyInstaller one-file payload follows the ELF image; stripping it could
# damage the archive, so skip the post-install strip and byte-compile steps.
%global __os_install_post %{nil}

%description
Albatross is a small arcade game: the player launches from a mountain, glides
over the valley and flaps to stay airborne. The game is a self-contained
PyInstaller build.

%install
install -Dm755 %{_sourcedir}/Albatross %{buildroot}%{_bindir}/albatross
install -Dm644 %{_sourcedir}/albatross.desktop %{buildroot}%{_datadir}/applications/albatross.desktop
for size in 16 24 32 48 64 128 256 512; do
  install -Dm644 %{_sourcedir}/icons/${size}x${size}/albatross.png \
    %{buildroot}%{_datadir}/icons/hicolor/${size}x${size}/apps/albatross.png
done

%files
%{_bindir}/albatross
%{_datadir}/applications/albatross.desktop
%{_datadir}/icons/hicolor/16x16/apps/albatross.png
%{_datadir}/icons/hicolor/24x24/apps/albatross.png
%{_datadir}/icons/hicolor/32x32/apps/albatross.png
%{_datadir}/icons/hicolor/48x48/apps/albatross.png
%{_datadir}/icons/hicolor/64x64/apps/albatross.png
%{_datadir}/icons/hicolor/128x128/apps/albatross.png
%{_datadir}/icons/hicolor/256x256/apps/albatross.png
%{_datadir}/icons/hicolor/512x512/apps/albatross.png

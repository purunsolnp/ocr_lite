@echo off
echo === Creating virtual environment for LibreTranslate ===

echo Creating virtual environment...
python -m venv libretranslate-env

echo Activating virtual environment...
call libretranslate-env\Scripts\activate

echo Installing packages in virtual environment...
pip install argostranslate libretranslate

echo.
echo Using argostranslate to download models...
python -c "import argostranslate.package; argostranslate.package.update_package_index(); available_packages = argostranslate.package.get_available_packages(); to_install = [pkg for pkg in available_packages if (pkg.from_code == 'en' and pkg.to_code == 'ko') or (pkg.from_code == 'ko' and pkg.to_code == 'en')]; print(f'Found {len(to_install)} packages to install:'); [print(f'- {pkg}') for pkg in to_install]; [pkg.install() for pkg in to_install]; print('Installation complete!')"

echo.
echo Checking installed packages...
python -c "import argostranslate.package; print('Installed packages:'); [print(f'{i}. {p}') for i, p in enumerate(argostranslate.package.get_installed_packages())]"

echo Deactivating virtual environment...
deactivate

echo.
echo Installation process completed!
echo Now you can run LibreTranslate with the run_libretranslate.bat script.
pause
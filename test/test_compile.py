# This file is part of arduino-cli.
#
# Copyright 2020 ARDUINO SA (http://www.arduino.cc/)
#
# This software is released under the GNU General Public License version 3,
# which covers the main part of arduino-cli.
# The terms of this license can be found at:
# https://www.gnu.org/licenses/gpl-3.0.en.html
#
# You can be released from the requirements of the above licenses by purchasing
# a commercial license. Buying such a license is mandatory if you want to modify or
# otherwise use the software for commercial activities involving the Arduino
# software without disclosing the source code of your own applications. To purchase
# a commercial license, send an email to license@arduino.cc.
import os
import platform
import tempfile
import hashlib
from pathlib import Path

import pytest

from .common import running_on_ci


def test_compile_without_fqbn(run_command):
    # Init the environment explicitly
    run_command("core update-index")

    # Install Arduino AVR Boards
    run_command("core install arduino:avr@1.8.3")

    # Build sketch without FQBN
    result = run_command("compile")
    assert result.failed


def test_compile_with_simple_sketch(run_command, data_dir, working_dir):
    # Init the environment explicitly
    run_command("core update-index")

    # Download latest AVR
    run_command("core install arduino:avr")

    sketch_name = "CompileIntegrationTest"
    sketch_path = Path(data_dir, sketch_name)
    fqbn = "arduino:avr:uno"

    # Create a test sketch
    result = run_command(f"sketch new {sketch_path}")
    assert result.ok
    assert f"Sketch created in: {sketch_path}" in result.stdout

    # Build sketch for arduino:avr:uno
    result = run_command(f"compile -b {fqbn} {sketch_path}")
    assert result.ok

    # Verifies expected binaries have been built
    sketch_path_md5 = hashlib.md5(bytes(sketch_path)).hexdigest().upper()
    build_dir = Path(tempfile.gettempdir(), f"arduino-sketch-{sketch_path_md5}")
    assert (build_dir / f"{sketch_name}.ino.eep").exists()
    assert (build_dir / f"{sketch_name}.ino.elf").exists()
    assert (build_dir / f"{sketch_name}.ino.hex").exists()
    assert (build_dir / f"{sketch_name}.ino.with_bootloader.bin").exists()
    assert (build_dir / f"{sketch_name}.ino.with_bootloader.hex").exists()

    # Verifies binaries are not exported by default to Sketch folder
    sketch_build_dir = Path(sketch_path, "build", fqbn.replace(":", "."))
    assert not (sketch_build_dir / f"{sketch_name}.ino.eep").exists()
    assert not (sketch_build_dir / f"{sketch_name}.ino.elf").exists()
    assert not (sketch_build_dir / f"{sketch_name}.ino.hex").exists()
    assert not (sketch_build_dir / f"{sketch_name}.ino.with_bootloader.bin").exists()
    assert not (sketch_build_dir / f"{sketch_name}.ino.with_bootloader.hex").exists()


@pytest.mark.skipif(
    running_on_ci() and platform.system() == "Windows",
    reason="Test disabled on Github Actions Win VM until tmpdir inconsistent behavior bug is fixed",
)
def test_output_flag_default_path(run_command, data_dir, working_dir):
    # Init the environment explicitly
    run_command("core update-index")

    # Install Arduino AVR Boards
    run_command("core install arduino:avr@1.8.3")

    # Create a test sketch
    sketch_path = os.path.join(data_dir, "test_output_flag_default_path")
    fqbn = "arduino:avr:uno"
    result = run_command("sketch new {}".format(sketch_path))
    assert result.ok

    # Test the --output-dir flag defaulting to current working dir
    result = run_command("compile -b {fqbn} {sketch_path} --output-dir test".format(fqbn=fqbn, sketch_path=sketch_path))
    assert result.ok
    target = os.path.join(working_dir, "test")
    assert os.path.exists(target) and os.path.isdir(target)


def test_compile_with_sketch_with_symlink_selfloop(run_command, data_dir):
    # Init the environment explicitly
    run_command("core update-index")

    # Install Arduino AVR Boards
    run_command("core install arduino:avr@1.8.3")

    sketch_name = "CompileIntegrationTestSymlinkSelfLoop"
    sketch_path = os.path.join(data_dir, sketch_name)
    fqbn = "arduino:avr:uno"

    # Create a test sketch
    result = run_command("sketch new {}".format(sketch_path))
    assert result.ok
    assert "Sketch created in: {}".format(sketch_path) in result.stdout

    # create a symlink that loops on himself
    loop_file_path = os.path.join(sketch_path, "loop")
    os.symlink(loop_file_path, loop_file_path)

    # Build sketch for arduino:avr:uno
    result = run_command("compile -b {fqbn} {sketch_path}".format(fqbn=fqbn, sketch_path=sketch_path))
    # The assertion is a bit relaxed in this case because win behaves differently from macOs and linux
    # returning a different error detailed message
    assert "Error during sketch processing" in result.stderr
    assert not result.ok

    sketch_name = "CompileIntegrationTestSymlinkDirLoop"
    sketch_path = os.path.join(data_dir, sketch_name)
    fqbn = "arduino:avr:uno"

    # Create a test sketch
    result = run_command("sketch new {}".format(sketch_path))
    assert result.ok
    assert "Sketch created in: {}".format(sketch_path) in result.stdout

    # create a symlink that loops on the upper level
    loop_dir_path = os.path.join(sketch_path, "loop_dir")
    os.mkdir(loop_dir_path)
    loop_dir_symlink_path = os.path.join(loop_dir_path, "loop_dir_symlink")
    os.symlink(loop_dir_path, loop_dir_symlink_path)

    # Build sketch for arduino:avr:uno
    result = run_command("compile -b {fqbn} {sketch_path}".format(fqbn=fqbn, sketch_path=sketch_path))
    # The assertion is a bit relaxed also in this case because macOS behaves differently from win and linux:
    # the cli does not follow recursively the symlink til breaking
    assert "Error during sketch processing" in result.stderr
    assert not result.ok


def test_compile_blacklisted_sketchname(run_command, data_dir):
    """
    Compile should ignore folders named `RCS`, `.git` and the likes, but
    it should be ok for a sketch to be named like RCS.ino
    """
    # Init the environment explicitly
    run_command("core update-index")

    # Install Arduino AVR Boards
    run_command("core install arduino:avr@1.8.3")

    sketch_name = "RCS"
    sketch_path = os.path.join(data_dir, sketch_name)
    fqbn = "arduino:avr:uno"

    # Create a test sketch
    result = run_command("sketch new {}".format(sketch_path))
    assert result.ok
    assert "Sketch created in: {}".format(sketch_path) in result.stdout

    # Build sketch for arduino:avr:uno
    result = run_command("compile -b {fqbn} {sketch_path}".format(fqbn=fqbn, sketch_path=sketch_path))
    assert result.ok


@pytest.mark.skip()
def test_compile_without_precompiled_libraries(run_command, data_dir):
    # Init the environment explicitly
    url = "https://adafruit.github.io/arduino-board-index/package_adafruit_index.json"
    result = run_command("core update-index --additional-urls={}".format(url))
    assert result.ok
    # arduino:mbed 1.1.5 is incompatible with the Arduino_TensorFlowLite library
    # see: https://github.com/arduino/ArduinoCore-nRF528x-mbedos/issues/93
    result = run_command("core install arduino:mbed@1.1.4 --additional-urls={}".format(url))
    assert result.ok
    result = run_command("core install arduino:samd@1.8.7 --additional-urls={}".format(url))
    assert result.ok
    result = run_command("core install adafruit:samd@1.6.0 --additional-urls={}".format(url))
    assert result.ok

    # Install pre-release version of Arduino_TensorFlowLite (will be officially released
    # via lib manager after https://github.com/arduino/arduino-builder/issues/353 is in)
    import zipfile

    with zipfile.ZipFile("test/testdata/Arduino_TensorFlowLite.zip", "r") as zip_ref:
        zip_ref.extractall("{}/libraries/".format(data_dir))
    result = run_command("lib install Arduino_LSM9DS1@1.1.0")
    assert result.ok
    result = run_command(
        "compile -b arduino:mbed:nano33ble {}/libraries/Arduino_TensorFlowLite/examples/magic_wand/".format(data_dir)
    )
    assert result.ok
    result = run_command(
        "compile -b adafruit:samd:adafruit_feather_m4 {}/libraries/Arduino_TensorFlowLite/examples/magic_wand/".format(
            data_dir
        )
    )
    assert result.ok

    # Non-precompiled version of Arduino_TensorflowLite
    result = run_command("lib install Arduino_TensorflowLite@1.15.0-ALPHA")
    assert result.ok
    result = run_command(
        "compile -b arduino:mbed:nano33ble {}/libraries/Arduino_TensorFlowLite/examples/magic_wand/".format(data_dir)
    )
    assert result.ok
    result = run_command(
        "compile -b adafruit:samd:adafruit_feather_m4 {}/libraries/Arduino_TensorFlowLite/examples/magic_wand/".format(
            data_dir
        )
    )
    assert result.ok

    # Bosch sensor library
    result = run_command('lib install "BSEC Software Library@1.5.1474"')
    assert result.ok
    result = run_command(
        "compile -b arduino:samd:mkr1000 {}/libraries/BSEC_Software_Library/examples/basic/".format(data_dir)
    )
    assert result.ok
    result = run_command(
        "compile -b arduino:mbed:nano33ble {}/libraries/BSEC_Software_Library/examples/basic/".format(data_dir)
    )
    assert result.ok


def test_compile_with_build_properties_flag(run_command, data_dir, copy_sketch):
    # Init the environment explicitly
    assert run_command("core update-index")

    # Install Arduino AVR Boards
    assert run_command("core install arduino:avr@1.8.3")

    sketch_path = copy_sketch("sketch_with_single_string_define")
    fqbn = "arduino:avr:uno"

    # Compile using a build property with quotes
    res = run_command(
        f"compile -b {fqbn} "
        + '--build-properties="build.extra_flags=\\"-DMY_DEFINE=\\"hello world\\"\\"" '
        + f"{sketch_path} --verbose --clean"
    )
    assert res.failed
    assert "Flag --build-properties has been deprecated, please use --build-property instead." not in res.stderr

    # Try again with quotes
    res = run_command(
        f"compile -b {fqbn} "
        + '--build-properties="build.extra_flags=-DMY_DEFINE=\\"hello\\"" '
        + f"{sketch_path} --verbose --clean"
    )
    assert res.failed
    assert "Flag --build-properties has been deprecated, please use --build-property instead." not in res.stderr

    # Try without quotes
    sketch_path = copy_sketch("sketch_with_single_int_define")
    res = run_command(
        f"compile -b {fqbn} "
        + '--build-properties="build.extra_flags=-DMY_DEFINE=1" '
        + f"{sketch_path} --verbose --clean"
    )
    assert res.ok
    assert "Flag --build-properties has been deprecated, please use --build-property instead." in res.stderr
    assert "-DMY_DEFINE=1" in res.stdout

    sketch_path = copy_sketch("sketch_with_multiple_int_defines")
    res = run_command(
        f"compile -b {fqbn} "
        + '--build-properties="build.extra_flags=-DFIRST_PIN=1,compiler.cpp.extra_flags=-DSECOND_PIN=2" '
        + f"{sketch_path} --verbose --clean"
    )
    assert res.ok
    assert "Flag --build-properties has been deprecated, please use --build-property instead." in res.stderr
    assert "-DFIRST_PIN=1" in res.stdout
    assert "-DSECOND_PIN=2" in res.stdout


def test_compile_with_build_property_containing_quotes(run_command, data_dir, copy_sketch):
    # Init the environment explicitly
    assert run_command("core update-index")

    # Install Arduino AVR Boards
    assert run_command("core install arduino:avr@1.8.3")

    sketch_path = copy_sketch("sketch_with_single_string_define")
    fqbn = "arduino:avr:uno"

    # Compile using a build property with quotes
    res = run_command(
        f"compile -b {fqbn} "
        + '--build-property="build.extra_flags=\\"-DMY_DEFINE=\\"hello world\\"\\"" '
        + f"{sketch_path} --verbose"
    )
    assert res.ok
    assert '-DMY_DEFINE=\\"hello world\\"' in res.stdout


def test_compile_with_multiple_build_property_flags(run_command, data_dir, copy_sketch, working_dir):
    # Init the environment explicitly
    assert run_command("core update-index")

    # Install Arduino AVR Boards
    assert run_command("core install arduino:avr@1.8.3")

    sketch_path = copy_sketch("sketch_with_multiple_defines")
    fqbn = "arduino:avr:uno"

    # Compile using multiple build properties separated by a space
    res = run_command(
        f"compile -b {fqbn} "
        + '--build-property="compiler.cpp.extra_flags=\\"-DPIN=2 -DSSID=\\"This is a String\\"\\"" '
        + f"{sketch_path} --verbose --clean"
    )
    assert res.failed

    # Compile using multiple build properties separated by a space and properly quoted
    res = run_command(
        f"compile -b {fqbn} "
        + '--build-property="compiler.cpp.extra_flags=-DPIN=2 \\"-DSSID=\\"This is a String\\"\\"" '
        + f"{sketch_path} --verbose --clean"
    )
    assert res.ok
    assert '-DPIN=2 "-DSSID=\\"This is a String\\""' in res.stdout

    # Tries compilation using multiple build properties separated by a comma
    res = run_command(
        f"compile -b {fqbn} "
        + '--build-property="compiler.cpp.extra_flags=\\"-DPIN=2,-DSSID=\\"This is a String\\"\\"\\" '
        + f"{sketch_path} --verbose --clean"
    )
    assert res.failed

    res = run_command(
        f"compile -b {fqbn} "
        + '--build-property="compiler.cpp.extra_flags=\\"-DPIN=2\\"" '
        + '--build-property="compiler.cpp.extra_flags=\\"-DSSID=\\"This is a String\\"\\"" '
        + f"{sketch_path} --verbose --clean"
    )
    assert res.failed
    assert "-DPIN=2" not in res.stdout
    assert '-DSSID=\\"This is a String\\"' in res.stdout

    res = run_command(
        f"compile -b {fqbn} "
        + '--build-property="compiler.cpp.extra_flags=\\"-DPIN=2\\"" '
        + '--build-property="build.extra_flags=\\"-DSSID=\\"hello world\\"\\"" '
        + f"{sketch_path} --verbose --clean"
    )
    assert res.ok
    assert "-DPIN=2" in res.stdout
    assert '-DSSID=\\"hello world\\"' in res.stdout


def test_compile_with_output_dir_flag(run_command, data_dir):
    # Init the environment explicitly
    run_command("core update-index")

    # Download latest AVR
    run_command("core install arduino:avr")

    sketch_name = "CompileWithOutputDir"
    sketch_path = Path(data_dir, sketch_name)
    fqbn = "arduino:avr:uno"

    # Create a test sketch
    result = run_command(f"sketch new {sketch_path}")
    assert result.ok
    assert f"Sketch created in: {sketch_path}" in result.stdout

    # Test the --output-dir flag with absolute path
    output_dir = Path(data_dir, "test_dir", "output_dir")
    result = run_command(f"compile -b {fqbn} {sketch_path} --output-dir {output_dir}")
    assert result.ok

    # Verifies expected binaries have been built
    sketch_path_md5 = hashlib.md5(bytes(sketch_path)).hexdigest().upper()
    build_dir = Path(tempfile.gettempdir(), f"arduino-sketch-{sketch_path_md5}")
    assert (build_dir / f"{sketch_name}.ino.eep").exists()
    assert (build_dir / f"{sketch_name}.ino.elf").exists()
    assert (build_dir / f"{sketch_name}.ino.hex").exists()
    assert (build_dir / f"{sketch_name}.ino.with_bootloader.bin").exists()
    assert (build_dir / f"{sketch_name}.ino.with_bootloader.hex").exists()

    # Verifies binaries are exported when --output-dir flag is specified
    assert output_dir.exists()
    assert output_dir.is_dir()
    assert (output_dir / f"{sketch_name}.ino.eep").exists()
    assert (output_dir / f"{sketch_name}.ino.elf").exists()
    assert (output_dir / f"{sketch_name}.ino.hex").exists()
    assert (output_dir / f"{sketch_name}.ino.with_bootloader.bin").exists()
    assert (output_dir / f"{sketch_name}.ino.with_bootloader.hex").exists()


def test_compile_with_export_binaries_flag(run_command, data_dir):
    # Init the environment explicitly
    run_command("core update-index")

    # Download latest AVR
    run_command("core install arduino:avr")

    sketch_name = "CompileWithExportBinariesFlag"
    sketch_path = Path(data_dir, sketch_name)
    fqbn = "arduino:avr:uno"

    # Create a test sketch
    assert run_command("sketch new {}".format(sketch_path))

    # Test the --output-dir flag with absolute path
    result = run_command(f"compile -b {fqbn} {sketch_path} --export-binaries")
    assert result.ok
    assert Path(sketch_path, "build").exists()
    assert Path(sketch_path, "build").is_dir()

    # Verifies binaries are exported when --export-binaries flag is set
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.eep").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.elf").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.hex").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.with_bootloader.bin").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.with_bootloader.hex").exists()


def test_compile_with_custom_build_path(run_command, data_dir):
    # Init the environment explicitly
    run_command("core update-index")

    # Download latest AVR
    run_command("core install arduino:avr")

    sketch_name = "CompileWithBuildPath"
    sketch_path = Path(data_dir, sketch_name)
    fqbn = "arduino:avr:uno"

    # Create a test sketch
    result = run_command(f"sketch new {sketch_path}")
    assert result.ok
    assert f"Sketch created in: {sketch_path}" in result.stdout

    # Test the --build-path flag with absolute path
    build_path = Path(data_dir, "test_dir", "build_dir")
    result = run_command(f"compile -b {fqbn} {sketch_path} --build-path {build_path}")
    print(result.stderr)
    assert result.ok

    # Verifies expected binaries have been built to build_path
    assert build_path.exists()
    assert build_path.is_dir()
    assert (build_path / f"{sketch_name}.ino.eep").exists()
    assert (build_path / f"{sketch_name}.ino.elf").exists()
    assert (build_path / f"{sketch_name}.ino.hex").exists()
    assert (build_path / f"{sketch_name}.ino.with_bootloader.bin").exists()
    assert (build_path / f"{sketch_name}.ino.with_bootloader.hex").exists()

    # Verifies there are no binaries in temp directory
    sketch_path_md5 = hashlib.md5(bytes(sketch_path)).hexdigest().upper()
    build_dir = Path(tempfile.gettempdir(), f"arduino-sketch-{sketch_path_md5}")
    assert not (build_dir / f"{sketch_name}.ino.eep").exists()
    assert not (build_dir / f"{sketch_name}.ino.elf").exists()
    assert not (build_dir / f"{sketch_name}.ino.hex").exists()
    assert not (build_dir / f"{sketch_name}.ino.with_bootloader.bin").exists()
    assert not (build_dir / f"{sketch_name}.ino.with_bootloader.hex").exists()


def test_compile_with_export_binaries_env_var(run_command, data_dir, downloads_dir):
    # Init the environment explicitly
    run_command("core update-index")

    # Download latest AVR
    run_command("core install arduino:avr")

    sketch_name = "CompileWithExportBinariesEnvVar"
    sketch_path = Path(data_dir, sketch_name)
    fqbn = "arduino:avr:uno"

    # Create a test sketch
    assert run_command("sketch new {}".format(sketch_path))

    env = {
        "ARDUINO_DATA_DIR": data_dir,
        "ARDUINO_DOWNLOADS_DIR": downloads_dir,
        "ARDUINO_SKETCHBOOK_DIR": data_dir,
        "ARDUINO_SKETCH_ALWAYS_EXPORT_BINARIES": "true",
    }
    # Test compilation with export binaries env var set
    result = run_command(f"compile -b {fqbn} {sketch_path}", custom_env=env)
    assert result.ok
    assert Path(sketch_path, "build").exists()
    assert Path(sketch_path, "build").is_dir()

    # Verifies binaries are exported when export binaries env var is set
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.eep").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.elf").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.hex").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.with_bootloader.bin").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.with_bootloader.hex").exists()


def test_compile_with_export_binaries_config(run_command, data_dir, downloads_dir):
    # Init the environment explicitly
    run_command("core update-index")

    # Download latest AVR
    run_command("core install arduino:avr")

    sketch_name = "CompileWithExportBinariesConfig"
    sketch_path = Path(data_dir, sketch_name)
    fqbn = "arduino:avr:uno"

    # Create a test sketch
    assert run_command("sketch new {}".format(sketch_path))

    # Create settings with export binaries set to true
    env = {
        "ARDUINO_DATA_DIR": data_dir,
        "ARDUINO_DOWNLOADS_DIR": downloads_dir,
        "ARDUINO_SKETCHBOOK_DIR": data_dir,
        "ARDUINO_SKETCH_ALWAYS_EXPORT_BINARIES": "true",
    }
    assert run_command("config init --dest-dir .", custom_env=env)

    # Test compilation with export binaries env var set
    result = run_command(f"compile -b {fqbn} {sketch_path}")
    assert result.ok
    assert Path(sketch_path, "build").exists()
    assert Path(sketch_path, "build").is_dir()

    # Verifies binaries are exported when export binaries env var is set
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.eep").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.elf").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.hex").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.with_bootloader.bin").exists()
    assert (sketch_path / "build" / fqbn.replace(":", ".") / f"{sketch_name}.ino.with_bootloader.hex").exists()


def test_compile_with_custom_libraries(run_command, copy_sketch):
    # Init the environment explicitly
    assert run_command("update")

    # Creates config with additional URL to install necessary core
    url = "http://arduino.esp8266.com/stable/package_esp8266com_index.json"
    assert run_command(f"config init --additional-urls {url}")

    # Install core to compile
    assert run_command("core install esp8266:esp8266")

    sketch_path = copy_sketch("sketch_with_multiple_custom_libraries")
    fqbn = "esp8266:esp8266:nodemcu:xtal=80,vt=heap,eesz=4M1M,wipe=none,baud=115200"

    first_lib = Path(sketch_path, "libraries", "Lib1")
    second_lib = Path(sketch_path, "libraries", "Lib2")
    # This compile command has been taken from this issue:
    # https://github.com/arduino/arduino-cli/issues/973
    assert run_command(f"compile --libraries {first_lib},{second_lib} -b {fqbn} {sketch_path}")

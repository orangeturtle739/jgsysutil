cmake_minimum_required(VERSION 3.16.3)
project(jgsysutil VERSION 0.1.0 LANGUAGES NONE)

find_package(unicmake REQUIRED)

find_program(CRYPTSETUP cryptsetup REQUIRED)
find_program(DD dd REQUIRED)
find_program(FREE free REQUIRED)
find_program(GDISK gdisk REQUIRED)
find_program(LVCREATE lvcreate REQUIRED)
find_program(MKDIR mkdir REQUIRED)
find_program(MKFS_EXT4 mkfs.ext4 REQUIRED)
find_program(MKFS_FAT mkfs.fat REQUIRED)
find_program(MKSWAP mkswap REQUIRED)
find_program(MOUNT mount REQUIRED)
find_program(UMOUNT umount REQUIRED)
find_program(OPENSSL openssl REQUIRED)
find_program(SHRED shred REQUIRED)
find_program(PVCREATE pvcreate REQUIRED)
find_program(RSYNC rsync REQUIRED)
find_program(SWAPON swapon REQUIRED)
find_program(SWAPOFF swapoff REQUIRED)
find_program(VGCREATE vgcreate REQUIRED)
find_program(VGCHANGE vgchange REQUIRED)
find_program(LVDISPLAY lvdisplay REQUIRED)
find_program(LOSETUP losetup REQUIRED)
find_program(LSBLK lsblk REQUIRED)
configure_file(${PROJECT_SOURCE_DIR}/src/jgsysutil/commands.py.in ${PROJECT_SOURCE_DIR}/src/jgsysutil/commands.py)

configure_file(
    ${PROJECT_SOURCE_DIR}/VERSION.in
    ${PROJECT_SOURCE_DIR}/VERSION
    @ONLY
)

add_custom_command(
    COMMAND touch ${CMAKE_CURRENT_SOURCE_DIR}/setup.py.stamp
    OUTPUT ${CMAKE_CURRENT_SOURCE_DIR}/setup.py.stamp
    DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/VERSION ${CMAKE_CURRENT_SOURCE_DIR}/setup.py
    VERBATIM
)

unicmake_python(
    PACKAGE_NAME jgsysutil
    SETUP_STAMP ${CMAKE_CURRENT_SOURCE_DIR}/setup.py.stamp
    ROOTS integration test
)

install(
    DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/integration
    DESTINATION ${CMAKE_INSTALL_PREFIX}/lib/jgsysutil_test
    USE_SOURCE_PERMISSIONS
)

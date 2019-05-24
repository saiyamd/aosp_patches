# aosp_tools
Script to auto generate aosp patches from repo

Script to generate patches from AOSP source.

This script compares base commit from manifest.xml of each project against head commit. If head commit is different from the manifest.xml, it generates the patches, create directory in provided output patch directory and moves those patches.

Test it on your repo and suggest edit.

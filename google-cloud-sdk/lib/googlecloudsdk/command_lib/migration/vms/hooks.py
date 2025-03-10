# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Argument processors for migration vms surface arguments."""

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties


# Helper Functions
def _GetMessageClass(msg_type_name):
  """Gets API message object for given message type name."""
  msg = apis.GetMessagesModule('vmmigration', 'v1')
  return getattr(msg, msg_type_name)


# Argument Processors
def GetDataDiskImageImportTransform(value):
  """Returns empty DataDiskImageImport entry."""
  del value
  data_disk_image_import = _GetMessageClass('DataDiskImageImport')
  return data_disk_image_import()


# Argument Processors
def GetSkipOsAdaptationTransform(value):
  """Returns empty SkipOsAdaptationTransform entry."""
  del value
  skip_os_adaptation = _GetMessageClass('SkipOsAdaptation')
  return skip_os_adaptation()


def GetEncryptionTransform(value):
  """Returns empty Encryption entry."""
  del value
  encryption = _GetMessageClass('Encryption')
  return encryption()


def SetLocationAsGlobal():
  """Set default location to global."""
  return 'global'


# Modify Request Hook For Disk Image Import
def FixCreateDiskImageImportRequest(ref, args, req):
  """Fixes the Create Image Import request for disk image import."""
  if not (args.generalize or args.license_type or args.boot_conversion):
    req.imageImport.diskImageTargetDefaults.osAdaptationParameters = None

  if not args.image_name:
    req.imageImport.diskImageTargetDefaults.imageName = ref.Name()

  if args.kms_key:
    req.imageImport.diskImageTargetDefaults.encryption = (
        GetEncryptionTransform(
            req.imageImport.diskImageTargetDefaults.encryption
            )
        )
    req.imageImport.diskImageTargetDefaults.encryption.kmsKey = args.kms_key

    req.imageImport.encryption = (
        GetEncryptionTransform(req.imageImport.encryption)
        )
    req.imageImport.encryption.kmsKey = args.kms_key

  FixTargetDetailsCommonFields(
      ref, args, req.imageImport.diskImageTargetDefaults
  )

  return req


# Modify Request Hook For Machine Image Import
def FixCreateMachineImageImportRequest(ref, args, req):
  """Fixes the Create Image Import request machine image import."""

  if not args.machine_image_name:
    req.imageImport.machineImageTargetDefaults.machineImageName = ref.Name()

  if not args.generalize and not args.license_type and not args.boot_conversion:
    req.imageImport.machineImageTargetDefaults.osAdaptationParameters = None

  if (
      not args.secure_boot
      and not args.enable_vtpm
      and not args.enable_integrity_monitoring
  ):
    req.imageImport.machineImageTargetDefaults.shieldedInstanceConfig = None

  if args.kms_key:
    req.imageImport.machineImageTargetDefaults.encryption = (
        GetEncryptionTransform(
            req.imageImport.machineImageTargetDefaults.encryption
            )
        )
    req.imageImport.machineImageTargetDefaults.encryption.kmsKey = args.kms_key

    req.imageImport.encryption = (
        GetEncryptionTransform(req.imageImport.encryption)
        )
    req.imageImport.encryption.kmsKey = args.kms_key

  FixTargetDetailsCommonFields(
      ref, args, req.imageImport.machineImageTargetDefaults
  )

  return req


def FixTargetDetailsCommonFields(ref, args, target_details):
  """"Fixes the target details common fields."""

  if not args.target_project:
    # Handle default target project being the host project.
    target = args.project or properties.VALUES.core.project.Get(required=True)
    target_details.targetProject = (
        ref.Parent().Parent().RelativeName() +
        '/locations/global/targetProjects/' + target
    )
  elif '/' not in args.target_project:
    # Handle prepending path to target project short-name.
    target_details.targetProject = (
        ref.Parent().Parent().RelativeName() +
        '/locations/global/targetProjects/' + args.target_project
    )

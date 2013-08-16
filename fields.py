#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tom
#
# Created:     16/04/2013
# Copyright:   (c) tom 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import arcpy

def addMissingFieldsToTarget(inputTable, targetTable, excludeList): #For the purpose of loading data from inputTable to targetTable
    returnFields = []
    targetDesc = arcpy.Describe(targetTable)
    inputDesc = arcpy.Describe(inputTable)
    for field in inputDesc.fields:
        if field.type != 'OID' and field.type != 'Geometry' and field.name != 'Shape_Length' and field.name != 'OBJECTID':
            if not field.name in excludeList:
                ##arcpy.AddMessage('Adding field ' + field.name + ' of type ' + field.type)
                returnFields += [field.name]
                if field.name in targetDesc.fields:
                    arcpy.DeleteField_management(targetTable, field.name)
                ##if not field.name in targetDesc.fields:
                try:
                    arcpy.AddField_management(targetTable, field.name, field.type, field.precision, field.scale, field.length, field.aliasName)
                except:
                    arcpy.AddWarning('Unable to add field ' + field.name + ' to ' + targetTable)
    return returnFields

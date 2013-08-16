#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      tom
#
# Created:     14/11/2012
# Copyright:   (c) tom 2012
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import arcpy,os

def CopyDomainsBetweenTables(inputTable, outputTable):
    inGDB = os.path.split(inputTable)[0]
    outGDB = os.path.split(outputTable)[0]
    arcpy.env.overwriteOutput = True
    dscOutWorkspace = arcpy.Describe(outGDB)
    domainList = []
    domainDict = dict()
    fieldList = arcpy.ListFields(inputTable)
    for field in fieldList:
        if field.domain:
            print("{0} has domain {1}"
              .format(field.name, field.domain))

            if not (field.domain in dscOutWorkspace.domains):
                arcpy.DomainToTable_management(inGDB, field.domain, "IN_MEMORY/DomainTab", "Code", "Description")
                arcpy.TableToDomain_management("IN_MEMORY/DomainTab", "Code", "Description", outGDB, field.domain)
                arcpy.AddMessage("Added " + field.domain + " to " + outGDB)
            domainDict[field.name] = field.domain
            domainList += [field.domain]
    fieldList = arcpy.ListFields(outputTable)
    for field in fieldList:
        if not field.domain and domainDict.has_key(field.name):
            arcpy.AssignDomainToField_management(outputTable, field.name, domainDict[field.name])
            arcpy.AddMessage("Assigned " + field.domain + " to " + outputTable)

    arcpy.SetParameterAsText(2, outputTable)

if __name__ == '__main__':
    inTable = arcpy.GetParameterAsText(0)
    outTable = arcpy.GetParameterAsText(1)
    CopyDomainsBetweenTables(inTable, outTable)

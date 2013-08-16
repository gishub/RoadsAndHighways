import arcpy, os, sys, traceback, GenerateRAndHSchema, CreateAndReplaceRoadsAndHighwayIndexes as idx, string, fields

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [createALRSFromFC]
        # Here is a test comment


class createALRSFromFC(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create ALRS From Feature Class and Calibration"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        paramOutGDB = arcpy.Parameter(
            displayName='Output Geodatabase',
            name='outWorkspace',
            datatype='DEWorkspace',
            parameterType='Required',
            direction='Input')

        paramInputLineFC = arcpy.Parameter(
            displayName='Input Line Feature Class',
            name='inLineFC',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Input')
        paramInputLineFC.filter.list = ["Polyline"]

        paramRouteIDField = arcpy.Parameter(
            displayName='Route ID Field',
            name='in_routeIDField',
            datatype='Field',
            parameterType='Required',
            direction='Input')
        paramRouteIDField.filter.list = ['Short', 'Long', 'Text', 'GUID']
        paramRouteIDField.parameterDependencies = [paramInputLineFC.name]

        paramRouteFromDateField = arcpy.Parameter(
            displayName='From Date Field',
            name='in_fromDateField',
            datatype='Field',
            parameterType='Required',
            direction='Input')
        paramRouteFromDateField.filter.list = ['Date', 'Text']
        paramRouteFromDateField.parameterDependencies = [paramInputLineFC.name]

        paramRouteToDateField = arcpy.Parameter(
            displayName='To Date Field',
            name='in_toDateField',
            datatype='Field',
            parameterType='Required',
            direction='Input')
        paramRouteToDateField.filter.list = ['Date', 'Text']
        paramRouteToDateField.parameterDependencies = [paramInputLineFC.name]

        paramDefaultFromDate = arcpy.Parameter(
            displayName='Default From Date',
            name='in_defaultDate',
            datatype='GPDate',
            parameterType='Required',
            direction='Input')
        paramDefaultFromDate.value = "1/1/1970"

        paramInputCalibrationPoint = arcpy.Parameter(
            displayName='Calibration Point Feature Class',
            name='inCalibrationPoint',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Input')
        paramInputCalibrationPoint.filter.list = ["Point"]

        paramCalPointMField = arcpy.Parameter(
            displayName='Calibration Point Measure Field',
            name='in_calPointMField',
            datatype='Field',
            parameterType='Required',
            direction='Input')
        paramCalPointMField.filter.list = ['Double']
        paramCalPointMField.parameterDependencies = [paramInputCalibrationPoint.name]

        paramNewALRSNetworkName = arcpy.Parameter(
            displayName='New LRS Network (LRM) Name',
            name='in_newLRSNetName',
            datatype='GPString',
            parameterType='Required',
            direction='Input')

        paramNewALRSNetworkID = arcpy.Parameter(
            displayName='New LRS Network ID',
            name='in_newLRSNetID',
            datatype='GPLong',
            parameterType='Required',
            direction='Input')
        paramNewALRSNetworkID.value = 1

        paramResultGDB = arcpy.Parameter(
            displayName='ALRS Geodatabase',
            name='outResultGDB',
            datatype='DEWorkspace',
            parameterType='Derived',
            direction='Output')

        params = [paramOutGDB,paramInputLineFC,paramRouteIDField,paramRouteFromDateField,paramRouteToDateField,paramDefaultFromDate,paramInputCalibrationPoint,paramCalPointMField,paramNewALRSNetworkName,paramNewALRSNetworkID,paramResultGDB]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        try:

            outGDBFullPath = parameters[0].valueAsText
    ##        outGDBName = arcpy.GetParameterAsText(1)
            inputFC= parameters[1].valueAsText
            routeFieldName = parameters[2].valueAsText
            fromDateField = parameters[3].valueAsText
            toDateField = parameters[4].valueAsText
            defaultFromDate = parameters[5].valueAsText
            inputCalibrationFC = parameters[6].valueAsText
            inputCalibrationMField = parameters[7].valueAsText
            lrsNetworks = [parameters[8].valueAsText]

            inputDsc = arcpy.Describe(inputFC)
            sr = inputDsc.spatialReference

            #Get the route ID field from the source so we can create the schema using the same field length
            routeField = arcpy.ListFields(inputFC, routeFieldName)[0]
            lrsActivities = ['Calibrate Route', 'Cartographic Realignment', 'Create Route', 'Extend Route', 'Realign Gap Route', 'Realign Overlapping Route', 'Realign Route', 'Reassign Route', 'Retire Route', 'Reverse Route', 'Shorten Route']

            arcpy.AddMessage('Creating Roads and Highways schema')
            GenerateRAndHSchema.makeALRS(outGDBFullPath,sr,lrsNetworks, lrsActivities, routeField.length)
            tempFC = os.path.join(outGDBFullPath, 'TempInput')
            routeTable = os.path.join(outGDBFullPath, 'Route')
            centerlineFC = os.path.join(outGDBFullPath, 'Centerline')
            centerlineSequence = os.path.join(outGDBFullPath, 'CenterlineSequence')
            calibrationPoint = os.path.join(outGDBFullPath, 'CalibrationPoint')
            #Delete the routeID from the route and calibration point feature classes so they can take on the route ID of the source
            arcpy.DeleteField_management(routeTable, ['ROUTEID'])
            upperInputFieldNames = []
            for field in inputDsc.fields:
                upperInputFieldNames += [field.name.upper()]
            if 'ROUTENAME' in upperInputFieldNames:
                arcpy.DeleteField_management(routeTable, ['ROUTENAME'])
                arcpy.AddMessage('Deleted ROUTENAME')
            arcpy.DeleteField_management(calibrationPoint, ['ROUTEID'])

            arcpy.AddMessage('Loading routes')
            routeFields = fields.addMissingFieldsToTarget(inputFC, routeTable, [fromDateField, toDateField])
            #inFeatures = arcpy.da.SearchCursor(inputFC, routeFields)
            routeTableCursor = arcpy.InsertCursor(routeTable)
            cCursor = arcpy.InsertCursor(centerlineFC)
            csCursor = arcpy.InsertCursor(centerlineSequence)
            arcpy.AddMessage('Writing routes.')
            x = 1
            cursorFields = routeFields
            useDefaultFromDate = True
            hasToDateField = False
            try:
                if fromDateField is not None and fromDateField != '' and fromDateField != '#':
                    cursorFields += [fromDateField]
                    useDefaultFromDate = False
                if toDateField is not None and toDateField != '' and toDateField != '#':
                    cursorFields += [toDateField]
                    hasToDateField = True
                cursorFields += ["SHAPE@"]

                with arcpy.da.SearchCursor(inputFC, cursorFields) as inFeatures:
                    cursorFieldDict = {}
                    for i, field in enumerate(cursorFields):
                        cursorFieldDict[field] = i

                    for feature in inFeatures:
                        arcpy.AddMessage('Loading route with RouteID ' + str(feature.getValue(routeFieldName)))
                        newRoute = routeTableCursor.newRow()
                        newRouteString = ""
                        for i, field in enumerate(cursorFields):
                            if i == 0:
                                newRouteString = feature[i]
                            else:
                                newRouteString += "," + feature[i]

                        routeTableCursor.insertRow(newRoute)
                        newCS = csCursor.newRow()
                        newCS.ROUTEID = feature.getValue(routeFieldName)
                        newCS.FROMDATE = defaultFromDate
                        newCS.ROADWAYID = x
                        newCS.NETWORKID = 1
                        csCursor.insertRow(newCS)
                        newCenterline = cCursor.newRow()
                        newCenterline.Shape = feature.getValue(inputDsc.shapeFieldName)
                        newCenterline.RoadwayID = x
                        newCenterline.FROMDATE = defaultFromDate
                        cCursor.insertRow(newCenterline)
                        x += 1
            finally:
                del routeTableCursor
                del cCursor
                del csCursor

            #Load calibration points
            arcpy.AddMessage('Loading calibration points')
            calibrationFields = fields.addMissingFieldsToTarget(inputCalibrationFC, calibrationPoint, [inputCalibrationMField])
            inCalCursor = arcpy.SearchCursor(inputCalibrationFC)
            outCalCursor = arcpy.InsertCursor(calibrationPoint)

            try:
                for calPnt in inCalCursor:
                    newCal = outCalCursor.newRow()
                    for field in calibrationFields:
                        ##arcpy.AddMessage('Calculating calibration point field: ' + field)
                        newCal.setValue(field, calPnt.getValue(field))
                    newCal.MEASURE = calPnt.getValue(inputCalibrationMField)
                    newCal.NETWORKID = 1
                    newCal.Shape = calPnt.Shape
                    outCalCursor.insertRow(newCal)
            finally:
                del inCalCursor
                del outCalCursor

            #Build indexes
            idx.RecreateIndexes(centerlineSequence, calibrationPoint, routeTable, [routeFieldName])

            #Set file geodatabase as output
            arcpy.SetParameterAsText(9, outGDBFullPath)
        except GenerateRAndHSchema.DataExistsError:
            pass
        except arcpy.ExecuteError:
            msgs = arcpy.GetMessages(2)
            arcpy.AddError(msgs)
        except:
            # Get the traceback object
            tb = sys.exc_info()[2]
            tbinfo = traceback.format_tb(tb)[0]

            # Concatenate information together concerning the error into a message string
            pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
            msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"

            # Return python error messages for use in script tool or Python Window
            arcpy.AddError(pymsg)
            arcpy.AddError(msgs)
        return

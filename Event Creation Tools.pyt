import arcpy, math, numpy, os

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create Events At Interval"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        paramRouteFLayer = arcpy.Parameter(
            displayName='Route Layer',
            name='in_routeLayer',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Input')

        paramRouteIDField = arcpy.Parameter(
            displayName='RouteID Field',
            name='in_routeIDField',
            datatype='Field',
            parameterType='Required',
            direction='Input')

        paramRouteIDField.filter.list = ['Short', 'Long', 'Text']
        paramRouteIDField.parameterDependencies = [paramRouteFLayer.name]

        paramInterval = arcpy.Parameter(
            displayName='Interval to create events',
            name='in_numberDeicmals',
            datatype='GPDouble',
            parameterType='Required',
            direction='Input')

        paramInterval.value = 1.0

        paramReportTable = arcpy.Parameter(
            displayName='Event Table',
            name='out_reportTable',
            datatype='DETable',
            parameterType='Required',
            direction='Output')

        params = [paramRouteFLayer, paramRouteIDField, paramInterval, paramReportTable]
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
        inputRouteFLayer = parameters[0].valueAsText
        inputRouteIDField = parameters[1].valueAsText
        inputInterval = parameters[2].valueAsText
        outTable = parameters[3].valueAsText
        fields = [inputRouteIDField, "SHAPE@"]

        # For each row print the WELL_ID and WELL_TYPE fields, and the
        #  the feature's x,y coordinates
        #
        outPathTuple = os.path.split(outTable)
        arcpy.CreateTable_management(outPathTuple[0], outPathTuple[1])
        arcpy.AddField_management(outTable, "RouteId", "TEXT", field_length=75)
        arcpy.AddField_management(outTable, 'Measure',"DOUBLE")
        eventCursor = None
        try:
            eventCursor = arcpy.da.InsertCursor(outTable, ("RouteId", "Measure"))

            with arcpy.da.SearchCursor(inputRouteFLayer, fields) as cursor:
                #totalRows = len(cursor)
                rowCount = 0
                for row in cursor:
                    line = row[1]
                    rowCount += 1
                    #arcpy.AddMessage("{0} starts at {1} and goes to {2}".format(row[0], line.firstPoint.M, line.lastPoint.M))
                    firstMeasure = float(line.firstPoint.M)
                    lastMeasure = float(line.lastPoint.M)
                    measureArray = numpy.arange(firstMeasure, lastMeasure, float(inputInterval))
                    if (len(measureArray) > 1 and measureArray[len(measureArray) - 1] != lastMeasure):
                        measureArray = numpy.append(measureArray, lastMeasure)
                    for m in measureArray:
                        #arcpy.AddMessage("{0} at measure {1}".format(row[0], m))
                        eventCursor.insertRow((row[0], m))
                    if(rowCount % 1000 == 0):
                            arcpy.AddMessage("Processed {0}".format(rowCount))
                    #print("{0}".format(row[0]))
        finally:
            del eventCursor

        return

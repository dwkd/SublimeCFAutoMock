import sublime, sublime_plugin
import math
import re

class cfautomockCommand(sublime_plugin.TextCommand):
	
	def run(self, edit):

		def getDummyValueForType(cftype):
			typeValues = { 'any' : '\"\"', 'array' : '[]', 'binary' : 'toBinary(toBase64(\"a\"))', 'boolean' : 'true', 'date' : 'Now()', 'guid' : 'CreateUUID()', 'numeric' : '0', 'query' : 'QueryNew(\"col\",\"int\")', 'string' : '\"\"', 'struct' : '{}', 'uuid' : 'CreateUUID()', 'xml' : '\"<a></a>\"' }
			return typeValues[cftype]

		def getArguments(method,requiredOnly=False):
			arguments = []

			cfarguments = self.view.find_all("<cfargument[\s\S]*?>")

			re_LookFor_ArgName = re.compile("name\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_ArgType = re.compile("type\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_requiredTrue = re.compile("required\s*\=\s*[\"\'](true|yes|1)", re.IGNORECASE)
			re_LookFor_sQuote = re.compile("[\'\" ]", re.IGNORECASE)
			supportedArgumentTypes = ['any','array','binary','boolean','date','guid','numeric','query','string','struct','uuid','xml']

			for argindex,argument in enumerate(cfarguments):
				if requiredOnly == True:
					if argument.intersects(method) and re_LookFor_requiredTrue.search(self.view.substr(argument)):						
						for key in self.view.substr(argument).split():

							# remove quotes and dbl quotes
							value = re.sub("[\'\" ]","",str(key)) 

							if re_LookFor_ArgName.search(key):						

								# remove name=
								NameValue = re.sub("name\=","",str(value)) 

							if re_LookFor_ArgType.search(key):

								# remove type=
								TypeValue = re.sub("type\=","",str(value)) 
						
						# store the supported argument name and type
						if TypeValue.lower() in supportedArgumentTypes:
							arguments.append([NameValue,TypeValue.lower()])
				else:
					if argument.intersects(method):						
						for key in self.view.substr(argument).split():

							# remove quotes and dbl quotes
							value = re.sub("[\'\" ]","",str(key)) 

							if re_LookFor_ArgName.search(key):						

								# remove name=
								NameValue = re.sub("name\=","",str(value)) 

							if re_LookFor_ArgType.search(key):

								# remove type=
								TypeValue = re.sub("type\=","",str(value)) 
						
						# store the supported argument name and type
						if TypeValue.lower() in supportedArgumentTypes:
							arguments.append([NameValue,TypeValue.lower()])

			return arguments

		#write general stats
		f = self.view
		returnMessage = ""
		returnMessage = "\nCFAutoMock \n\nGeneral Stats:\n==========================================================================================================================\n"
		returnMessage += "File: "+str(f.file_name())+"\nSize: ~"+str(f.size()/1024)+"Kb ("+str(f.size())+" bytes)\n"
		all = self.view.find_all("[\s\S]*")
		self.view.add_regions("AllContent", all, "source", sublime.HIDDEN)
		g = self.view.get_regions("AllContent")
		for allregion in g:
			h = len(self.view.substr(allregion))
		
		#get all functions
		allMethods = self.view.find_all("<cffunction[\s\S]*?<\/cffunction>", sublime.IGNORECASE)

		PublicMethodIndexes = []
		PrivateMethodIndexes = []
		RemoteMethodIndexes = []
		PackageMethodIndexes = []

		#loop through functions and find all private and remote functions
		for idx,method in enumerate(allMethods):
			methodLineByLine = self.view.split_by_newlines(method)
			re_accessPublic = re.compile("access\s*\=\s*[\"\'](public)[\"\']", re.IGNORECASE)
			re_accessRemote = re.compile("access\s*\=\s*[\"\'](remote)[\"\']", re.IGNORECASE)
			re_accessPrivate = re.compile("access\s*\=\s*[\"\'](private)[\"\']", re.IGNORECASE)
			re_accessPackage = re.compile("access\s*\=\s*[\"\'](package)[\"\']", re.IGNORECASE)

			for line in methodLineByLine:
				foundAccessPublic = re_accessPublic.search(self.view.substr(line))
				if foundAccessPublic:
					PublicMethodIndexes.append(idx)					
			
			for line in methodLineByLine:
				foundAccessRemote = re_accessRemote.search(self.view.substr(line))
				if foundAccessRemote:
					RemoteMethodIndexes.append(idx)					

			for line in methodLineByLine:
				foundAccessPrivate = re_accessPrivate.search(self.view.substr(line))
				if foundAccessPrivate:
					PrivateMethodIndexes.append(idx)
			
			for line in methodLineByLine:
				foundAccessPackage = re_accessPackage.search(self.view.substr(line))
				if foundAccessPackage:
					PackageMethodIndexes.append(idx)


		returnMessage += "Methods:\n\t" + str(len(PublicMethodIndexes)) + " Public\n\t" + str(len(PrivateMethodIndexes)) + " Private\n\t" + str(len(RemoteMethodIndexes)) + " Remote\n\t" + str(len(PackageMethodIndexes)) + " Package"
		returnMessage += "\n==========================================================================================================================\n"
		
		ShellUnitTestsCollection = ""
		CompleteUnitTestsCollection = ""
		unitTestsTotal= 0
	
		

		# #############################
		# UNIT TEST SHELLS 
		# #############################

		# loop through methods and begin writing unit tests 
		for idx,method in enumerate(allMethods):

			MethodDetails = { 'Name' : '', 'Access' : 'public' }
			methodLineByLine = self.view.split_by_newlines(method)
			re_LookFor_MethodName = re.compile("name\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_Access = re.compile("access\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_Functions = re.compile("(?<!response)(?<!result)\.[A-Za-z\d_]+\(", re.IGNORECASE)

			# get the method name and access
			for line in methodLineByLine:				
				if not len(MethodDetails['Name']) and re_LookFor_MethodName.search(self.view.substr(line)):
					for splittedItem in self.view.substr(line).split():
						if re_LookFor_MethodName.search(splittedItem):
							MethodDetails['Name'] = re.sub(">","",str(splittedItem))
							MethodDetails['Name'] = re.sub("[\'\" ]","",str(MethodDetails['Name']))
							MethodDetails['Name'] = re.sub("name\=","",str(MethodDetails['Name']))
						elif re_LookFor_Access.search(splittedItem):
							MethodDetails['Access'] = re.sub(">","",str(splittedItem).lower())
							MethodDetails['Access'] = re.sub("[\'\" ]","",str(MethodDetails['Access']))
							MethodDetails['Access'] = re.sub("access\=","",str(MethodDetails['Access']))

		
			# gather all arguments
			arguments = getArguments(method)

			unitTest = ""
			unitTest += "\n\n\t<cffunction name=\"" + str(MethodDetails['Name']) + "_ValidArgs_ReturnsSuccess\" access=\"public\">"
			unitTest += "\n\t\t<cfscript>"
			unitTest += "\n\t\t\tvar Obj = __GetComponentToBeTested();"
			unitTest += "\n\t\t\tvar expected  = \"\";"
			if str(MethodDetails['Access']) == "private":
				unitTest += "\n\t\t\tmakePublic(Obj, \"" + str(MethodDetails['Name']) + "\");"

			# mock variables stored components and their methods
			VariablesScopeDendencies = re.findall(r'variables\.[^\.]*?\.[^\(]*?\([^\;]*?\;', self.view.substr(method), re.IGNORECASE)

			ComponentsToBeMocked = []
			ComponentMethodsToBeMocked = []
			for DependencyToMock in VariablesScopeDendencies:
				NameOfComponentToBeMocked = re.findall(r'(?<=variables\.).*?(?=\.)', DependencyToMock, re.IGNORECASE)
				NameOfComponentMethodToBeMocked = re.findall(r'(?<=\.)[^\.]*?(?=[\r\n]?\()', DependencyToMock, re.IGNORECASE)
				ArgsForComponentMethodToBeMocked = re.findall(r'(?<=[\(])[^;]*(?=\)\;)', DependencyToMock, re.IGNORECASE)
				if ArgsForComponentMethodToBeMocked[0]:
					NumberOfArgsForComponentMethodToBeMocked = len(ArgsForComponentMethodToBeMocked[0].strip().split(','))
				else:
					NumberOfArgsForComponentMethodToBeMocked = 0

				if NameOfComponentToBeMocked[0] and NameOfComponentMethodToBeMocked[0]:
					if {'ComponentName' : NameOfComponentToBeMocked[0], 'Scope' : 'variables'} not in ComponentsToBeMocked:
						ComponentsToBeMocked.append({'ComponentName' : NameOfComponentToBeMocked[0], 'Scope' : 'variables'})

					if {'ComponentName' : NameOfComponentToBeMocked[0], 'MethodName' : NameOfComponentMethodToBeMocked[0].strip(), 'NumberOfArgs' : NumberOfArgsForComponentMethodToBeMocked } not in ComponentMethodsToBeMocked:
						ComponentMethodsToBeMocked.append({'ComponentName' : NameOfComponentToBeMocked[0], 'MethodName' : NameOfComponentMethodToBeMocked[0].strip(), 'NumberOfArgs' : NumberOfArgsForComponentMethodToBeMocked })

				else:
					unitTest += "\n\t\t\t/* Failed to mock: " + str(DependencyToMock) + "*/"

			# write mocked methods
			for Component in ComponentsToBeMocked:
				unitTest += "\n\n\t\t\tvar " + str(Component['ComponentName']) + "Mock = mock();"
				
				for ComponentMethodToBeMocked in ComponentMethodsToBeMocked:
					if Component['ComponentName'] == ComponentMethodToBeMocked['ComponentName']:
						unitTest += "\n\t\t\tvar " + str(ComponentMethodToBeMocked['MethodName']) + "Return = \"\";"

				for ComponentMethodToBeMocked in ComponentMethodsToBeMocked:
					if Component['ComponentName'] == ComponentMethodToBeMocked['ComponentName']:
						unitTest += "\n\t\t\t" + str(Component['ComponentName']) + "Mock." + str(ComponentMethodToBeMocked['MethodName']) + "(" + ','.join(["\"{any}\"" for a in range(0,ComponentMethodToBeMocked['NumberOfArgs'])]) + ").returns(" + str(ComponentMethodToBeMocked['MethodName']) + "Return);"

				unitTest += "\n\t\t\tinjectProperty(Obj, \"" + str(Component['ComponentName']) + "\", " + str(Component['ComponentName']) + "Mock, \"" + str(Component['Scope'])  + "\");"

			# write actual 
			unitTest += "\n\n\t\t\tvar actual = Obj." + str(MethodDetails['Name'])
			unitTest += "\n\t\t\t(" 
			
			for oindex,argument in enumerate(arguments):
				unitTest += "\n\t\t\t\t" + argument[0] + " = " + getDummyValueForType(argument[1])
				if oindex+1 < len(arguments):
					unitTest += ","					

			unitTest += "\n\t\t\t);"
			unitTest += "\n\n\t\t\tAssert(actual eq expected,\"Expected something but got something else\");"
			unitTest += "\n\t\t</cfscript>"
			unitTest += "\n\t</cffunction>"
			ShellUnitTestsCollection += unitTest
			unitTestsTotal += 1

			


		# #############################
		# COMPLETE UNIT TESTS
		# #############################

		# loop through methods and begin writing unit tests 
		for idx,method in enumerate(allMethods):

			MethodDetails = { 'Name' : '', 'Access' : 'public' }
			methodLineByLine = self.view.split_by_newlines(method)
			re_LookFor_MethodName = re.compile("name\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_Access = re.compile("access\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_Functions = re.compile("(?<!response)(?<!result)\.[A-Za-z\d_]+\(", re.IGNORECASE)

			# get the method name and access
			for line in methodLineByLine:				
				if not len(MethodDetails['Name']) and re_LookFor_MethodName.search(self.view.substr(line)):
					for splittedItem in self.view.substr(line).split():
						if re_LookFor_MethodName.search(splittedItem):
							MethodDetails['Name'] = re.sub(">","",str(splittedItem))
							MethodDetails['Name'] = re.sub("[\'\" ]","",str(MethodDetails['Name']))
							MethodDetails['Name'] = re.sub("name\=","",str(MethodDetails['Name']))
						elif re_LookFor_Access.search(splittedItem):
							MethodDetails['Access'] = re.sub(">","",str(splittedItem).lower())
							MethodDetails['Access'] = re.sub("[\'\" ]","",str(MethodDetails['Access']))
							MethodDetails['Access'] = re.sub("access\=","",str(MethodDetails['Access']))

			# create missing arg unit test
			
			arguments = getArguments(method, True)

			for argument in arguments:
				unitTest = ""
				unitTest += "\n\n\t<cffunction name=\"" + str(MethodDetails['Name']) + "_MissingArg_" + argument[0] + "_ReturnsException\" access=\"public\" mxunit:expectedException=\"Coldfusion.runtime.MissingArgumentException\">"
				if str(MethodDetails['Access']) == "private" or str(MethodDetails['Access']) == "package":
					unitTest += "\n\t\t<cfset makePublic(\"" + str(MethodDetails['Name']) + "\") />"

				unitTest += "\n\t\t<cfset variables.ComponentToBeTested." + str(MethodDetails['Name'])
				unitTest += "\n\t\t(" 
				
				otherarguments = list(arguments)
				otherarguments.remove(argument)

				for oindex,otherargument in enumerate(otherarguments):
					unitTest += "\n\t\t\t" + otherargument[0] + " = " + getDummyValueForType(otherargument[1])
					if oindex+1 < len(otherarguments):
						unitTest += ","					

				unitTest += "\n\t\t) />"
				unitTest += "\n\t</cffunction>"
				CompleteUnitTestsCollection += unitTest
				unitTestsTotal += 1
		

		returnMessage += "\n<cfcomponent extends=\"unittests.myTestCasesConfig\">"
		returnMessage += "\n\n\t<!--------------------------------------------------------------------------"
		returnMessage += "\n\tSection: Public methods"
		returnMessage += "\n\t--------------------------------------------------------------------------->"
		returnMessage += "\n\n\t<cffunction name=\"Setup\" access=\"public\">"
		returnMessage += "\n\t\t<cfset variables.ComponentToBeTested = __GetComponentToBeTested() />"
		returnMessage += "\n\t</cffunction>"
		returnMessage += "\n\n\t<cffunction name=\"TearDown\" access=\"public\">"
		returnMessage += "\n\t\t<cfset StructDelete(variables, \"ComponentToBeTested\") />"
		returnMessage += "\n\t</cffunction>\n"
		returnMessage += "\n\n\n\t<!--------------------------------------------------------------------------"
		returnMessage += "\n\tSection: Unit Test Shells - These unit tests must be finished by the end user."
		returnMessage += "\n\t--------------------------------------------------------------------------->"
		returnMessage += ShellUnitTestsCollection
		returnMessage += "\n\n\n\t<!--------------------------------------------------------------------------"
		returnMessage += "\n\tSection: Complete Unit Tests"
		returnMessage += "\n\t--------------------------------------------------------------------------->"
		returnMessage += CompleteUnitTestsCollection
		returnMessage += "\n\n\n\t<!--------------------------------------------------------------------------"
		returnMessage += "\n\tSection: Private methods"
		returnMessage += "\n\t--------------------------------------------------------------------------->"
		returnMessage += "\n\n\t<cffunction name=\"__GetComponentToBeTested\" access=\"private\">"
		returnMessage += "\n\t\t<cfreturn CreateObject(\"component\",\"path.to.ComponentToBeTested\") />"
		returnMessage += "\n\t</cffunction>"
		returnMessage += "\n\n</cfcomponent>"
		#send to new file
		w = self.view.window()
		w.run_command("new_file")
		v = w.active_view()
		v.insert(edit,0,returnMessage)

		
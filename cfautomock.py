import sublime, sublime_plugin
import math
import re


class cfautomockCommand(sublime_plugin.TextCommand):
	
	def run(self, edit):

		def getDummyValueForType(cftype):
			typeValues = { 'any' : '\"\"', 'array' : '[]', 'binary' : 'toBinary(toBase64(\"a\"))', 'boolean' : 'true', 'date' : 'Now()', 'guid' : 'CreateUUID()', 'numeric' : '0', 'query' : 'QueryNew(\"col\",\"int\")', 'string' : '\"\"', 'struct' : '{}', 'uuid' : 'CreateUUID()', 'xml' : '\"<a></a>\"' }
			return typeValues[cftype]

		#write general stats
		f = self.view
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
		
		unitTestsCollection = ""
		unitTestsTotal= 0

		# search for all cfarguments
		cfarguments = self.view.find_all("<cfargument[\s\S]*?>")

		# loop through methods and begin writing unit tests 
		for idx,method in enumerate(allMethods):
			dependencies = []
			QueryDependencies = []
			MethodDetails = { 'Name' : '', 'Access' : 'public' }
			methodLineByLine = self.view.split_by_newlines(method)
			re_LookFor_MethodName = re.compile("name\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_Access = re.compile("access\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_CreateObject = re.compile("CreateObject", re.IGNORECASE)
			re_LookFor_Functions = re.compile("(?<!response)(?<!result)\.[A-Za-z\d_]+\(", re.IGNORECASE)
			get_allQueryDependencies = self.view.find_all("<cfquery[\s\S]*?<\/cfquery>", sublime.IGNORECASE)

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
			arguments = []

			re_LookFor_ArgName = re.compile("name\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_ArgType = re.compile("type\s*\=\s*[\"\']", re.IGNORECASE)
			re_LookFor_requiredTrue = re.compile("required\s*\=\s*[\"\'](true|yes|1)", re.IGNORECASE)
			re_LookFor_sQuote = re.compile("[\'\" ]", re.IGNORECASE)
			supportedArgumentTypes = ['any','array','binary','boolean','date','guid','numeric','query','string','struct','uuid','xml']

			for argindex,argument in enumerate(cfarguments):
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
			
			# create missing arg unit test
			for argument in arguments:
				unitTest = ""
				unitTest += "\n\n\t<cffunction name=\"" + str(MethodDetails['Name']) + "_MissingArg_" + argument[0] + "_ReturnsException\" access=\"public\" mxunit:expectedException=\"Coldfusion.runtime.MissingArgumentException\">"
				if str(MethodDetails['Access']) == "private":
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
				unitTestsCollection += unitTest
				unitTestsTotal += 1
		
		returnMessage += "Successfully built a total of " + str(unitTestsTotal) + " unit tests:"
		returnMessage += "\n==========================================================================================================================\n"
		returnMessage += "\n==========================================================================================================================\n"
		returnMessage += "Missing arguments unit tests:"
		returnMessage += "\n==========================================================================================================================\n"
		returnMessage += "\n\n\t<cffunction name=\"Setup\" access=\"public\">"
		returnMessage += "\n\t\t<cfset variables.ComponentToBeTested = __GetComponentToBeTested() />"
		returnMessage += "\n\t</cffunction>"
		returnMessage += "\n\n\t<cffunction name=\"TearDown\" access=\"public\">"
		returnMessage += "\n\t\t<cfset StructDelete(variables, \"ComponentToBeTested\") />"
		returnMessage += "\n\t</cffunction>"
		returnMessage += unitTestsCollection
		returnMessage += "\n\n\t<cffunction name=\"__GetComponentToBeTested\" access=\"private\">"
		returnMessage += "\n\t\t<cfreturn CreateObject(\"component\",\"path.to.component\") />"
		returnMessage += "\n\t</cffunction>"
		#send to new file
		w = self.view.window()
		w.run_command("new_file")
		v = w.active_view()
		v.insert(edit,0,returnMessage)

		
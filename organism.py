#!/usr/bin/python3
'''
	File includes two classes:
		Protein - used to store information about proteins found in organisms
		Organism - used to store information about organisms. Contains data structures identifying ncid's found in the organism and the proteins found in those ncid's.
'''
import sys
import re
from collections import defaultdict

from regex import *



'''
	Holds information identifying proteins. 
	Information includes:
		wp - protein id
		nc - sequence protein is found in
		position - position in nc sequence
		start - number of BP found before start of protein in nc
		end - number of BP ofund after end of protein in nc
		strand - positive or negative orientation
		sequence - bp or amino acids that compose protein
'''
class Protein:
	def __init__(self, wp, nc, sequence, position, start, end, strand):
		self.wp, self.nc, self.sequence, self.position, self.start, self.end, self.strand = wp, nc, sequence, int(position), int(start), int(end), strand





	'''
		Returns values for wp, nc, position, strand for a given protein instance
	'''
	def short_info(self):
		return '{0}\t{1}\t{2}\t{3}'.format(self.wp, self.nc, self.position, self.strand)





	'''
		toString equivalent printing more info than short_info()
	'''
	def __str__(self):
		return '{0}\t{1}\t{2}\t{3}'.format(self.short_info(), self.start, self.end, self.sequence)





'''
	Holds information about a specific organism.
	Information includes:
		Instance variables:
			totalCDS - all coding regions
			codingCDS - proteins (non pseudo)
			NC_ID_maps_PROTEINS - DICT. Uses ncid as key to hold a list of proteins found in that ncid
			NC_ID_maps_WP_ID - DICT. Uses ncid as key to hold a list of wp id's found in that ncid
			countPseudo - whether pseudo genes should increment position counter
			positionStartsAtZero - 
			(IMPORTANT: if trying to match up data, make sure both this script and the other source count pseudo (or don't) and start at the same place(positionStartsAtZero))
'''
class Organism:
	'''
	************************************************************************
	*			END OF METHODS THAT PARSE SPECIFIC FILES					
	************************************************************************
	'''



	def faa_join(self, WP_maps_SEQUENCE):
		for ncid in self.NC_ID_maps_PROTEINS.keys():
			for protein in self.NC_ID_maps_PROTEINS[ncid]:
				protein.sequence = WP_maps_SEQUENCE[protein.wp]





	def faa_read(self, faaFile, bufferSize, join = False):
		WP_maps_SEQUENCE = dict()
		wp, sequence = "", ""
		with open(faaFile, 'r', bufferSize) as handle:
			for line in handle:
				if line.startswith('>'):
					if sequence != "" and wp != "":
						WP_maps_SEQUENCE[wp] = sequence
					
					match = Regex.WP_REGEX.search(line)
					if match == None:
						cols = line.split('#')
						wp = 'Protein('
						wp += cols[1].strip()	# prodigal
						wp += '-'
						wp += cols[2].strip()
						wp += ')'
					else:
						wp = match.group(0)

					sequence = ""
				else:
					sequence += line.rstrip()

			if sequence != '' and wp != '':	# puts last remaining sequence/wp in dict (won't be caught in loop)
				WP_maps_SEQUENCE[wp] = sequence

		if join:
			self.faa_join(WP_maps_SEQUENCE)





	'''
	        self.countPseudo, self.positionStartsAtZero, self.bufferSize = countPseudo, positionStartsAtZero, bufferSize

			        self.NC_ID_maps_PROTEINS, self.NC_ID_maps_WP_ID = defaultdict(self.empty_list), defaultdict(self.empty_list)
					        self.totalCDS, self.codingCDS = 0, 0

	'''
	def gff_parse_ncid_cds(self, NCID_maps_CDS_LIST):
		for ncid, cdsList in NCID_maps_CDS_LIST.items():
			if self.positionStartsAtZero:
				position = 0
			else:
				positon = 1

			for cdsDict in cdsList:
				self.totalCDS += 1
				
				otherInfo = cdsDict['otherInfo']
				if 'pseudo=true' in otherInfo:
					if self.countPseudo:
						position += 1
				else:
					match = Regex.WP_REGEX.search(otherInfo)
					if match == None:
						wpid = 'Protein({0}-{1})'.format(cdsDict['start'], cdsDict['end'])
					else:
						wpid = match.group(0)
					self.codingCDS += 1
					self.NC_ID_maps_PROTEINS[ncid].append(Protein(wpid, ncid, "", position, cdsDict['start'], cdsDict['end'], cdsDict['strand'])) # Protein(wp, nc, sequence, position, start, end, strand)
					self.NC_ID_maps_WP_ID[ncid].append(wpid)
					
					
					position += 1



	def gff_read(self, gffFile, bufferSize):
		NCID_maps_CDS_LIST = defaultdict(self.empty_list)
		with open(gffFile, 'r', bufferSize) as handle:
			for line in handle:

				if 'CDS' not in line:
					continue

				cols = line.rstrip().split('\t')
				
				ncid, start, end, strand, otherInfo = cols[0], cols[3], cols[4], cols[6], cols[8]

				cds = { 'start': start, 'end': end, 'strand':strand, 'otherInfo': otherInfo }
				NCID_maps_CDS_LIST[ncid].append(cds)

		self.gff_parse_ncid_cds(NCID_maps_CDS_LIST)




	'''
	************************************************************************
	*						START GBFF PARSING METHODS
	************************************************************************
	'''

	'''
		Parsing gbff for proteins only considers CDS regions.
		This method is called when a new regions is found (CDS, gene, mRNA, etc).
		
		Params:
			saveNextRegion - BOOLEAN. Whether the nex region is important and should be saved (ie, next regions is a CDS region)
			region just read. Lines of text that include useful information about proteins.
			saving - BOOLEAN. Whether the region read is meant to be used or not.
			readRegion - STRING. Region just read. Lines of text that include useful information about proteins.
			ncid - STRING. Sequence ID region readRegion belongs to.
			NC_ID_maps_CDS_LIST - DICT. Listing of ncid's with all the CDS found within them.
	'''
	def gbff_done_reading_region(self, saveNextRegion, saving, readRegion, ncid, NC_ID_maps_CDS_LIST):
		'''
			If saving == true then it means readRegion is a CDS region (important).
			Breaks down the CDS region to only include information needed later (memory stuff).
		'''
		if saving:
			lines = readRegion.split('\n')
			shortVersion = lines[0] + '\n'
			
			secondPortion = 1
			isPseudo = False


			'''
				Breaks down CDS region.
			'''
			for num, line in enumerate(lines[1:]):
				if '/protein_id=' in line:
					secondPortion = num + 1
					break
				if '/pseudo' in line:
					secondPortion = num + 1
					isPseudo = True
					break
			if isPseudo:
				shortVersion = shortVersion + '\n' + lines[secondPortion] + '\n'
			else:
				shortVersion += '\n'.join(lines[secondPortion:])


			NC_ID_maps_CDS_LIST[ncid].append(shortVersion)
		return saveNextRegion, ""





	'''
		Method is called by gbff_parse_ncid_regions(). Method is only called if region is non pseudo.
		Parses a region to find useful information about a protien. 
		Using information gathered a new Protein object is created. 
		This protein object is appended to NC_ID_maps_PROTEINS DICT.
		The WP id is appended to NC_ID_maps_WP_ID
	'''
	def gbff_parse_region(self, cds, ncid, position):
		'''
			Finds protein sequence
		'''
		match = Regex.TRANSLATION_REGEX.search(cds)
		translation = match.group(1).replace('\n', "").replace(' ', "")

		'''
			Finds protein id
		'''
		match = Regex.PROTEIN_ID_REGEX.search(cds)
		wp = match.group(1)

		'''
			Finds proteins start/end position
		'''
		match = Regex.START_END_REGEX1.search(cds)
		start, end = match.group(1), match.group(2)

		'''
			Determines whether region is on pos or neg strand
		'''
		if 'complement' in cds:
			strand = '-'
		else:
			strand = '+'
		
		self.NC_ID_maps_PROTEINS[ncid].append(Protein(wp, ncid, translation, position, start, end, strand))	# Protein(wp, nc, sequence, position, start, end, strand)
		self.NC_ID_maps_WP_ID[ncid].append(wp)






	'''
		Parses cds regions saved in NC_ID_maps_CDS_LIST.
		Skips psuedo regions.
		Counts number of number of regions, number of coding regions, and the position of the protein.
		
		Params:
			NC_ID_maps_CDS_LIST - DICT. NC ID is used to map to a region, CDS (value). CDS contains information about a protein.
	'''
	def gbff_parse_ncid_regions(self, NC_ID_maps_CDS_LIST):
		for ncid, cdsList in NC_ID_maps_CDS_LIST.items():
			self.totalCDS += len(cdsList)	# counts all coding regions

			'''
				Whether user wants protein position to start at 0 or 1 this block sets the counter
			'''
			if self.positionStartsAtZero:
				position = 0
			else:
				position = 1


			'''
				Parses regions. Skips pseudo genes. Increments counter on pseudo genes if user specified it.
				Counts coding regions.
			'''
			for cds in cdsList:
				if '/pseudo' in cds:
					if self.countPseudo == True:	# increments position counter if user wanted
						position += 1
					continue

				self.codingCDS += 1	# increments counter of coding regions (non pseudo proteins)
				self.gbff_parse_region(cds, ncid, position)	# parses region
				position += 1	# increments position counter





	'''
		Called only when the user specifies a file that ends with .gbff
		Parse the gbff file accordingly.
	'''
	def gbff_read(self, gbffFile, bufferSize):
		NC_ID_maps_CDS_LIST = defaultdict(self.empty_list)

		'''
			Parses organism file.
		'''
		with open(gbffFile, 'r', bufferSize) as handle:
			'''
				saving - if CDS was read, the rest of the lines being read are going to be important. saving is a flag indicating the lines read are important
				Eg)
					CDS...... - saving = TRUE, REGION1 is important and should be parsed
					REGION1...
					GENE...... - saving = FALSE, REGION2 is unimportant and can be ignored
					REGION2...
					CDS....... - saving = TRUE, REGION3 is important and should be parsed
					REGION3...

			'''
			saving, readRegion, ncid = False, "", ""
			for line in handle:
				if line.startswith('     CDS'):	# start of important region
					saving, readRegion = self.gbff_done_reading_region(True, saving, readRegion, ncid, NC_ID_maps_CDS_LIST)
					readRegion += line
				elif line.startswith('                     '):	# portion of text containing useful information, eg) wp id, sequence..
					if saving:
						readRegion += line
				elif line.startswith('VERSION'):	# There are breaks between the file, there the ncid of the region is defined in a line that starts with word "VERSION", ncid is needed, ncid is obtained
					match = Regex.NC_REGEX.search(line)
					ncid = match.group(0)
				else:
					saving, readRegion = self.gbff_done_reading_region(False, saving, readRegion, ncid, NC_ID_maps_CDS_LIST)	# hits a non CDS region that also fails other previous condition (eg. GENE, tRNA, etc)


		self.gbff_parse_ncid_regions(NC_ID_maps_CDS_LIST)


	'''
	************************************************************************
	*						END GBFF PARSING METHODS
	************************************************************************
	'''






	'''
	************************************************************************
	*				END OF METHODS THAT PARSE SPECIFIC FILES
	************************************************************************
	'''





	'''
		Used in place of a lambda within defaultdicts. Allows organism object to be serializable by pickle and the faster cpickle.
	'''
	def empty_list(self):
		return []





	'''
		Creates Organism instance.

		Params:
			gbffFile - STRING. Input file to parse
			countPseudo - BOOLEAN. Whether pseudo genes increment counter keeping track of protein position. DEFAULT = TRUE
			positionStartsAtZero - BOOLEAN. Whether position of proteins should start at 0. DEFAULT = TRUE
	'''
	def __init__(self, organismFile, countPseudo = True, positionStartsAtZero = True, bufferSize = 8192, twoFileParse = False):
		self.countPseudo, self.positionStartsAtZero, self.bufferSize = countPseudo, positionStartsAtZero, bufferSize

		self.NC_ID_maps_PROTEINS, self.NC_ID_maps_WP_ID = defaultdict(self.empty_list), defaultdict(self.empty_list) 
		self.totalCDS, self.codingCDS = 0, 0


		if not twoFileParse:
			self.singleFileParse(organismFile)

		else:	# user wants to parse two data files together to get more information than one file can provide
			self.twoFileParse(organismFile)
		





	def singleFileParse(self, organismFile):
		if organismFile.endswith('.gbff'):
			self.gbff_read(organismFile, self.bufferSize)
		elif organismFile.endswith('.gff'):
			self.gff_read(organismFile, self.bufferSize)
		else:
			print('File format not supported')
			return

		match = Regex.GCF_REGEX.search(organismFile)
		if match == None:
			self.GCF = gffFile.split('.')
		else:
			self.GCF = match.group(0)



		


	def twoFileParse(self, organismFiles):
		if len(organismFiles) < 2:
			print('Need two files to parse two files...')
			return
			
			
		file1, file2 = organismFiles[0], organismFiles[1]
		if file1.endswith('.gff'):
			gffFile = file1
		elif file1.endswith('.gff'):
			gfffile = file2
		else:
			print('At least one file has to be gff')
			return

		if file1.endswith('.faa'):
			faaFile = file1
		elif file2.endswith('.faa'):
			faaFile = file2
		else:
			print('At least one file has to be faa')
			return

		self.gff_read(gffFile, self.bufferSize)
		self.faa_read(faaFile, self.bufferSize, join = True)

		match = Regex.GCF_REGEX.search(gffFile)
		if match == None:
			self.GCF = gffFile.split('.')[0].split('/')[-1]
		else:
			self.GCF = match.group(0)







	'''
		Returns a bit of info about an organism instance
	'''
	def short_info(self):
		return 'Total CDS: {0}\nTotal Coding CDS: {1}\nTotal NCIDs found: {2}'.format( str(self.totalCDS), str(self.codingCDS), str(len(self.NC_ID_maps_PROTEINS.keys())) )





	'''
		Prints string representation of instance.
	'''
	def __str__(self):
		proteinInfo = ""
		for ncid, proteins in self.NC_ID_maps_PROTEINS.items():
			for protein in proteins:
				proteinInfo += str(protein)
				proteinInfo += '\n'
		return '{0}\n{1}\n{2}'.format(self.short_info, '{0} protein found in {1}:'.format(len(proteins), ncid), proteinInfo)




	'''
		Finds position of given wp id and the ncid the protein is found in.

		Params:
			wp - protein id
	'''
	def find_nc_and_position_of_protein(self, wp):
		for ncidKey, wpList in self.NC_ID_maps_WP_ID.items():
			try:
				ncid, index = ncidKey, wpList.index(wp)
				return ncid, index
			except ValueError:
				continue
		return None, None




	'''
		Returns info about wp

		Params:
			wp - protein id
	'''
	def get_protein_info(self, wp):
		ncid, index = self.find_nc_and_position_of_protein(wp)
		return self.NC_ID_maps_PROTEINS[ncid][index].short_info()





	'''
		Returns upstream neighbors of given wp.

		Params:
			amount - how many proteins to acquire upstream
			startingWP - protein id to use to start neighborhood
			inclusive - whether startingWP should be inclueded in gene neighborhood
	'''
	def get_upstream_neighbors(self, amount, startingWP, inclusive=True):
		ncid, startingWPIndex = self.find_nc_and_position_of_protein(startingWP)
		if ncid == None or startingWPIndex == None:
			return []

		if inclusive:
			left, right = ( startingWPIndex - amount ), ( startingWPIndex + 1 )
		else:
			left, right = ( startingWPIndex - amount - 1 ), ( startingWPIndex)	# -1 includes one more protein (replacing startinWP)


		if left < 0:
			left = 0

		return self.NC_ID_maps_PROTEINS[ncid][left:right]





	'''
		Returns downstream neighbors of given wp.

		Params:
			amount - how many proteins to acquire downstream
			startingWP - protein id to use to start neighborhood
			inclusive - whether startingWP should be inclueded in gene neighborhood
	'''
	def get_downstream_neighbors(self, amount, startingWP, inclusive=True):
		ncid, startingWPIndex = self.find_nc_and_position_of_protein(startingWP)
		if ncid == None or startingWPIndex == None:
			return []

		
		if inclusive:
			left, right = startingWPIndex, ( startingWPIndex + amount + 1 )
		else:
			left, right = startingWPIndex + 1, ( startingWPIndex + amount + 2 )	# +2 includes one more protein (replacing startingWP)


		totalProteins = len(self.NC_ID_maps_PROTEINS[ncid])
		if right > totalProteins:
			right = totalProteins

		return self.NC_ID_maps_PROTEINS[ncid][left:right]




	'''
		Returns protein with given wp id

		Params:
			wp - protein id of protein wanted.
	'''
	def get_protein(self, wp):
		ncid, wpIndex = self.find_nc_and_position_of_protein(wp)
		if ncid == None or wpIndex == None:
			return None
	
		return self.NC_ID_maps_PROTEINS[ncid][wpIndex]


	def get_ncid_contents(self):
		return self.NC_ID_maps_PROTEINS

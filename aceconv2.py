from lxml import etree
from nltk import word_tokenize,sent_tokenize
import xml.etree.ElementTree as ET
import pickle
import sys


def save_pickle(data,outfile):
    pickle.dump( data, open( outfile, "wb" ) )
def load_pickle(filename):
    return pickle.load( open( filename, "rb" ) )

def xmltointer(xmlfile,rawfile,entypes):
	tree = ET.parse(xmlfile)
	treeraw=etree.parse(rawfile)
	rootraw=treeraw.getroot()
	root = tree.getroot()
	names=[]
	inds=[]
	typel=[]
	for doc in root.findall('document'):
		for entity in doc.findall('entity'):
		    type1= entity.get('TYPE')
		    if type1 in entypes:
		        mentions=entity.findall('entity_mention')
		        for ment in mentions:
		            mentype1=ment.get("TYPE")
		            if mentype1=="NAM":
		                extent1=ment.find("head")
		                charseq1=extent1.find("charseq")
		                names.append(charseq1.text)
		                inds.append((int(charseq1.get('START'))-1,int(charseq1.get('END'))))
		                typel.append(type1)
	body=rootraw.find("BODY")
	tex=[x for x in rootraw.itertext()]
	docid=rootraw.find("DOCID").text
	doctype=rootraw.find("DOCTYPE").text
	doctime=rootraw.find("DATETIME").text
	body=rootraw.find("BODY")
	headl=body.find("HEADLINE")
	head="heeead"
	if headl!=None:
		#print(headl.text)
		head=headl.text
	text1=""
	for x in tex[1:]:
		if x!=docid and x!=doctype and x!=doctime and x!=head:
			text1+=x
		else:
			text1+="!1"+x[2:-2]+"!1"
	#for x in tex[1:]:
	#	text1+=x
	#for t in tex:
	#   text1=text1+t
	return text1, names, inds ,typel

##in order this function to work
## the address of the file.tbl file must be givene
## returns the names of the files in the adj folders for English
def filenamelist(filelistfile):
    filenames=open(filelistfile).readlines()
    englishnames=[]
    for name in filenames:
        if "data/English" in name and ".apf.xml" in name and ".score" not in name and "adj" in name:
            englishnames.append(base+name[:name.find(".apf.xml")])
    return englishnames


##converts & in documents to &amp;
## this step is required for the .sgm files
## output files have the suffix .sgm1
def andsignupdate(filenames):
    for name in filenames:
        name1=name+".sgm"
        read1=open(name1).read()
        write1=open(name1+"1","w")
        for x in read1:
            if x=="&":
                write1.write("&amp;")
            else:
                write1.write(x)

def ACEtoInterCorpus(filelistfile,outfilename,entypes):
    filenames=filenamelist(filelistfile)
    andsignupdate(filenames)
    t=""
    names=[]
    inds=[]
    typelist=[]
    off=0
    begin="\n-DOCSTART-\n"
    for name in filenames:
        text1,names1,inds1,typel1 = xmltointer(name+".apf.xml",name+".sgm1",entypes)
        t+=begin
        t+=text1
        for name1 in names1:
            names.append(name1)
        for ind in inds1:
            inds.append((ind[0]+off+len(begin),ind[1]+off+len(begin)))
        for typ in typel1:
            typelist.append(typ)
        off+=len(text1)+len(begin)
    return t,names,inds,typelist

def findtupleind(list1,tok):
    for x in range(len(list1)):
        if list1[x][0]==tok:
            return x
    return -1

def merger(inds,typelist):
    list1=[]
    for x in range(len(inds)):
        list1.append((inds[x],typelist[x]))
    return list1

## create a corpus and mark the beginning and end of entities
## in sentence and token splitted form
## 1TAG Entity 1TAG is the tagging format
def markentities(rawtext,names,inds,typelist,outname):
	merged=merger(inds,typelist)
	#print(len(merged))
	merged.sort()
	out=open(outname,"w",encoding="utf-8")
	markedt=""
	ind1=0
	len1=len(rawtext)
	for i in range(len1):
		#print(merged[ind1][0])
		if i==int(merged[ind1][0][0]):
			tag=merged[ind1][1]
			out.write("1"+tag)
			markedt+="1"+tag
			#print(i)
		if i==int(merged[ind1][0][1]):
			tag=merged[ind1][1]
			out.write("1"+tag)
			markedt+="1"+tag
			if ind1< len(merged)-1:
				ind1+=1
				while(merged[ind1-1][0][0]==merged[ind1][0][0]) and ind1<len(merged)-1:
					ind1+=1
			#print(i)
		out.write(rawtext[i])
		markedt+=rawtext[i]
	return markedt


def subtractsub(str1,sub1):
    if str1.find(sub1)==0:
        return str1[len(sub1):]
    elif str1.find(sub1)!=-1:
        return str1[:-len(sub1)]
    return "-1"


##takes as input the marked rawtext and outputs the token-per-line corpus
## the code is not neat and will be updated
def markedtotokenperline(markedtext,entypes,outname,tagver):
	tags=[]
	out=open(outname,"w")
	for t1 in entypes:
		tags.append("1"+t1)
	sents=sent_tokenize(markedtext)
	for sent in sents:
		words=word_tokenize(sent)
		f=0
		tag=""
		for word in words:
			if "DOCSTART" in word:
				out.write(word + " O\n\n")
			else:
				if f==0:
					for t1 in tags:
						if t1 in word:
							f=1
							tag=t1[1:]
							break
					if f==0:
						out.write(word+" O\n")
					else:
						w1=subtractsub(word,"1"+tag)
						singtok=subtractsub(w1,"1"+tag)
						if singtok!="-1":
							f=0
							if tagver==0:
								out.write(singtok+" 1\n")
							else:
								out.write(singtok+" "+tag+"\n")
						else:
							if tagver==0:
								out.write(w1+" 1\n")
							else:
								out.write(w1+" "+tag+"\n")
				else:
					for t1 in tags:
						if t1 in word:
							f=0
							tag=t1[1:]
							break
					if f==0:
						w1=subtractsub(word,"1"+tag)
						if tagver==0:
							out.write(w1+" 1\n")
						else:
							out.write(w1+" "+tag+"\n")
					else:
						if tagver==0:
							out.write(word+" 1\n")
						else:       		
							out.write(word+" "+tag+"\n")
		out.write("\n")  
##delete all characters between special signs 
def deletemetadata(corpus,specsign):
	ind1=corpus.find(specsign)
	ind2=0
	ind=0
	text=""
	indprev=0
	while ind1<len(corpus)-5:
		ind2=corpus[ind1+1:].find(specsign)+ind1+1
		text+=corpus[ind:ind1]
		ind1=corpus[ind2+1:].find(specsign)+ind2+1
		ind=ind2+2
		if ind1-ind2-1==-1:
		    break
	text+=corpus[ind:]
	return text


##given an annotated corpus 
## change it to the BIO tagging format
def toBIOformat(corpusname,outname):
    corp=open(corpusname).readlines()
    out=open(outname,"w")
    ptag="O"
    for line in corp:
        if len(line)>1:
            ls=line.split()
            for x in ls[:-1]:
                out.write(x+" ")
            if ls[-1]!="O":
                if ptag==ls[-1]:
                    out.write("I-"+ptag+"\n")
                else:
                    out.write("B-"+ls[-1]+"\n")
            else:
                out.write("O\n")
            ptag=ls[-1]
        else:
            out.write(line)
            ptag="O"

def GPEtoLOC(corp,out):
	c1=open(corp).readlines()
	o1=open(out,"w")
	for line in c1:
		l=line.replace("B-GPE","B-LOC")
		l2=l.replace("I-GPE","I-LOC")
		o1.write(l2)
		
		
##not used
def fix1tag(filename,tagtypes,outname):
	corp=open(filename).readlines()
	out=open(outname,"w")
	for line in corp:
		ls=line.split()
		if len(ls)>1:
			token=ls[0]
			c=0
			for tag in tagtypes:
				tag1="1"+tag
				newtoken=token
				while tag1 in newtoken:
					c=1
					newtoken=""
					ind1=newtoken.find(tag1)
					newtoken+=newtoken[:ind1]
					newtoken+=newtoken[ind1+len(tag1):]
			if c==0:
				if token[-2:]!="1G":
					out.write(line)
			else: 
				out.write(newtoken+"\t"+ls[1]+"\n")
		else:
			out.write(line)
##takes as input the marked rawtext and outputs the token-per-line corpus
## the code is not neat and will be updated
def markedtotokenperline2(markedtext,entypes,outname):
	tags=[]
	out=open(outname,"w")
	for t1 in entypes:
		tags.append("1"+t1)
	sents=sent_tokenize(markedtext)
	for sent in sents:
		words=word_tokenize(sent)
		f=0
		tag=""
		for word in words:
			if "DOCSTART" in word:
				out.write(word + " O\n\n")
			else:
				c=0
				for tag in tags:
					if word.find(tag)!=-1:
						c=1
						out.write(word.replace(tag,"")+" "+tag[1:]+"\n")
				if c==0:
					out.write(word+" O\n")
		out.write("\n")
##save these variables
def ACEtotokenperlineconverter(filelistfile,interoutfilename,outfilename,tagtypes,tagver,finalout):
	filelist=filenamelist(filelistfile)
	t,names,inds,typelist=ACEtoInterCorpus(filelistfile,outfilename,tagtypes)
	markedtext=markentities(t,names,inds,typelist,interoutfilename)
	deletedt=deletemetadata(markedtext,"!1")
	markedtotokenperline2(deletedt,tagtypes,outfilename)
	toBIOformat(outfilename,outfilename+"BIO")
	#fix1tag(outfilename+"BIO",tagtypes,"1tagfixed")
	#GPEtoLOC(outfilename+"BIO",finalout)
	##metadataeraser not working properly because of tokenization
	###metadataeraser.deletemetadata(outfilename,filelist,"deletedcorp")
    
base="ACE/"
filelistfile="ACE/docs/file.tbl"
intoutn="out1"
outn="tokperlineCorpus"
finalout1="ACEconllformat"
tagtypes=["ORG","LOC","GPE","PER","FAC"]
tagver=1         
metadata=1


##save these variables




args=sys.argv
if len(args)>1:
	if args[1]=="-h":
		print("python3 aceconv2.py filelistfile outfilename tagtypes tagver | for custom mode")
		print("python3 aceconv2.py def  | for default mode")
	elif args[1]=="def":
		print("filelist address: ACE/docs/file.tbl")
		print("intermediate raw corpus: out1")
		print("corpus file name: tokperlineCorpus")
		print("Tag types: ORG LOC GPE PER FAC")
		#print("Conll format corpus name: "+"ACEconllformat")
		print("Tagging version: type-specific BIO format")
		print("metadata deleted")
		ACEtotokenperlineconverter(filelistfile,intoutn,outn,tagtypes,tagver,finalout1)
			
	else:
		tagtypes1=[]
		filelistfile1=args[1]
		outfilename1=args[2]
		interoutfilename="out1"
		for x in args[3:-1]:
			tagtypes1.append(x)
		tagver1=int(args[-1])
		
		
		
		
		
		
		#metadata1=int(args[-1])
		ACEtotokenperlineconverter(filelistfile1,interoutfilename,outfilename1,tagtypes1,tagver1)



import requests

# 
# https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/PMC10275820/ascii
def get_fulltext(pmcid,outdir=None):
    apiurl='https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/%s/ascii'
    xmltext=requests.get(apiurl % pmcid).text #.json()[0]['documents'][0]
    if xmltext.startswith('[Error] : No result can be found.'):
        print('No fulltext found for', pmcid)
        return None
    if outdir is not None:
        with open(f'{outdir}/{pmcid}.xml','wt') as fp:
            fp.write(xmltext)
    else:
        return xmltext

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from xml.etree import ElementTree as ET

import sys
sys.path.append('PyBioC/src')
sys.path.append('PyBioC/src/bioc')
sys.path.append('PyBioC/src/bioc/meta')
sys.path.append('PyBioC/src/bioc/compat')
import bioc
from bioc import BioCReader
from collections import defaultdict

def get_fulltext_from_xml(xmlname):
    # apiurl='https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_xml/%s/ascii'
    # xmltext=requests.get(apiurl % pubmedid).text #.json()[0]['documents'][0]
    # with open('tmp_output.xml','wt') as fp:
    #     fp.write(xmltext)

    bioc_reader = BioCReader(xmlname, dtd_valid_file='PyBioC/BioC.dtd')
    bioc_reader.read()

    breakflag = False
    continueflag = False

    fulltext = ''
    passages = defaultdict(list)

    for passage in bioc_reader.collection.documents[0].passages:
        stype = passage.infons['section_type']
        
        if stype=='FIG':
            continueflag=True
            # print('\tFIG',passage.text)

        if continueflag:
            continueflag=False
            continue

        # print(stype)
        # print(passage.text)
        fulltext += passage.text+'\n'
        passages[stype].append(passage.text)
        if breakflag:
            break
        if stype=='CONCL':
            breakflag=True

    return fulltext, dict(passages)

def get_title_and_atype(pmcid):
    """title and article type"""
    if pmcid[:3]=='PMC':
        pmcid = pmcid[3:]

    title = ''
    atype = ''
    
    apiurl='https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:%s&metadataPrefix=pmc_fm'

    try:
        paperdata=requests.get(apiurl % pmcid, verify=False, timeout=20).text
        
        root = ET.fromstring(paperdata)
        for child in root:
            if 'GetRecord' in child.tag:
                for elt in child.findall('{*}record//{*}article-meta//{*}article-title'):            
                    if elt.text is not None:
                        title += elt.text
                    if elt.tail is not None:
                        title += elt.tail
                        
                    for ch in elt:
                        if ch.text is not None:
                            title += ch.text
                        if ch.tail is not None:
                            title += ch.tail
                            
                for elt in child.findall('{*}record//{*}article-categories//{*}subj-group[@subj-group-type="heading"]/{*}subject'):
                    atype += elt.text+';'
    except:
        print('#')
        
    return title, atype

def get_abstract(pmcid):
    if pmcid[:3]=='PMC':
        pmcid = pmcid[3:]
    apiurl='https://www.ncbi.nlm.nih.gov/pmc/oai/oai.cgi?verb=GetRecord&identifier=oai:pubmedcentral.nih.gov:%s&metadataPrefix=pmc_fm'
    paperdata=requests.get(apiurl % pmcid, verify=False).text
    abs = ''
    root = ET.fromstring(paperdata)
    for child in root:
        if 'GetRecord' in child.tag:
            for elt in child.findall('{*}record//{*}article-meta//{*}abstract//'):            
                if 'sec' in elt.tag :
                    continue
                else:
                    if 'title' in elt.tag:
                        abs += '<h>'+elt.text+'<h>'
                    elif 'p' in elt.tag:
                        abs += '<p>'+elt.text+'<p>'
    return abs

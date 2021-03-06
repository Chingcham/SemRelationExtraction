import os
import sys
import re
import numpy
#import ipdb
#import cProfile
import time
import ipdb

class Datasets:
    
    """
    Combine all small chunk files and create the training smaples
    
    inputfolder: Folder containing splitfiles
    outfolder:  Folder to store output files
    minWordCount: threshold values for word count
    minPairCount: threshold values for pair count
    
    """
    
    def __init__(self, inputfolder, outfolder, windowSize, minWordCount, minPairCount):
        
        listfiles = os.listdir(inputfolder)
        self.outputfolder = outfolder+str(int(time.time()))
        os.mkdir(self.outputfolder)
        self.windowSize = windowSize
        
        self.posfile = self.outputfolder+'/Triplesets_positive'
        self.negfile = self.outputfolder+'/Triplesets_negative'
        self.statfile = self.outputfolder+"/Statistics"

        self.wdictfile = self.outputfolder+'/Word2Id'
        self.pdictfile = self.outputfolder+'/Pair2Id'
        
        wordfiles = []
        pairfiles = []
        
        self.word_frequency = dict()
        self.pair_frequency = dict()
        
       
        for files in listfiles:

            if re.search('_out$',files):
                pairfiles.append(inputfolder+files)

            if re.search('_out_word$',files):
                wordfiles.append(inputfolder+files)

        for wfile in wordfiles:
            self.combineWordsFrequencies(wfile)
        
        
        self.word2id = dict()
        self.id2word = dict()
        self.wid_frequency = dict()
            
        totalWords = self.words2Indices(minWordCount)
        
        self.init_sample_table()
        
        self.combinePairsFrequencies(pairfiles)
        
        self.pair2id = dict()
        self.id2pair = dict()
        
        self.pairs2Indices(minPairCount)
        
        
        
    def combineWordsFrequencies(self, wfile):
      
        """
            Create word_frequency dictionary for Vocabulary
        """
        with open(wfile) as inputFile:

            for lines in inputFile:
                item = lines.lower().strip().split()
                
                if item[0] in self.word_frequency:
                    self.word_frequency[item[0]] += int(item[1]) 
                else:
                    self.word_frequency[item[0]] = int(item[1])
                    
        
        inputFile.close()
        
    def combinePairsFrequencies(self, pairfiles):
        
        """
        Track pair frequency by comnbining all split files for pair 
        """
        ###
        self.initial_data_sets_file = self.outputfolder+'/InitialDatasets'
        try:
            os.remove(self.initial_data_sets_file)
        except:
            pass
        
        self.iDSFile = open(self.initial_data_sets_file,"a")
        
        ###
        for i,pfile in enumerate(pairfiles):
        
            testCount = 0
        
            with open(pfile) as inputFile:

                for lines in inputFile:
                    item = lines.lower().strip().split('\t\t')

                    if len(item) != 4:
                        print("Ëxceptional items!", item)
                        continue

                    distance = int(item[0])
                    #Check if the entry within window size, else break from further reading
                    if distance > self.windowSize:
                        break
                    
                    pair = item[1].split('\t')
                    
                    if len(pair) != 2:
                        print("Exceptional pairs",item[0])
                        continue

                    word1 = pair[0]
                    word2 = pair[1]

                    if word1 in self.word2id:
                        #does word1 satisfies minimum count?
                        wid1 = self.word2id[word1]
                    else:
                        continue


                    if word2 in self.word2id:
                        #does word2 satisfies minimum count?
                        wid2 = self.word2id[word2]
                    else:
                        continue

                    pairCount = int(item[2])

                    if (wid1,wid2) in self.pair_frequency:
                        self.pair_frequency[(wid1,wid2)] += pairCount
                        
                    else:
                        self.pair_frequency[(wid1,wid2)] = pairCount


                    words = item[3].split('\t')
                    
                    
                    
                    for w, wCount in zip(words[0::2], words[1::2]):
                        
                        if w in self.word2id:
                            in_wid = self.word2id[w]
                            
                        else:
                            continue
                            #in between word is too less in frequency, hence ignored from dataset.
                            
                        testCount += 1
                        
                        for _ in range(int(wCount)):
                            self.iDSFile.write(str(wid1)+':'+str(wid2)+':'+str(in_wid)+"\n")
                        
            inputFile.close()
            ###
            #print("\n",i+1," : ",pfile," Done . entries count of ",testCount)
            ###

        self.iDSFile.close()
        
        
    def words2Indices(self, wordCount):
        
        #Remove the file if it already exists
        try:
            os.remove(self.wdictfile)
        except:
            pass
            
        wid = 0
        outputFile = open(self.wdictfile,"a")
        for word in self.word_frequency:
            if self.word_frequency[word] >= wordCount:
                self.word2id[word] = wid
                self.id2word[wid] = word
                self.wid_frequency[wid] = self.word_frequency[word]
                
                outputFile.write(word+"\t"+str(wid)+"\n")
                wid += 1
        
        #Release memory
        
        self.word_frequency = dict()
        outputFile.close()
        temp = len(self.word2id)
        print("\n #With word frequency :", wordCount)
        print( "\n # Words : ", temp)
        return temp
        
    def init_sample_table(self):
        
        print("\n Making sample table")
        
        self.sample_table = []
        sample_table_size = 1e8
        
        pow_frequency = numpy.array(list(self.wid_frequency.values()))**0.75  # 3/4 of the power of pairs
        words_pow = sum(pow_frequency) # initial calculation
        ratio = pow_frequency / words_pow # initial calculation  
        count = numpy.round(ratio * sample_table_size) # This is for sampling indices on the same ratio over 1e8  # initial implementation

        for wid, c in enumerate(count):
            self.sample_table += [wid] * int(c)
                
        self.sample_table = numpy.array(self.sample_table)

        
    def pairs2Indices(self, pairCount):
        
        #Remove the file if it already exists
        try:
            os.remove(self.pdictfile)
        except:
            pass
        
        pid = 0
        outputFile = open(self.pdictfile,"a")
        
        for pair in self.pair_frequency:
            if self.pair_frequency[pair] >= pairCount:
                self.pair2id[pair] = pid
                self.id2pair[pid] = pair
                
                wid1 = pair[0]
                wid2 = pair[1]
                w1 = self.id2word[wid1]
                w2 = self.id2word[wid2]
                
                outputFile.write(w1+"\t"+w2+"\t"+str(pid)+"\n")
                
                pid += 1
    
        #Release memory
        self.pair_frequency.clear()
        outputFile.close()
        print("\n #With pair frequency : ",pairCount)
        print( "\n # Pairs : ", len(self.pair2id))  
        
        

                           
    #generate 'k'negative samples for every positive sample        
    def get_neg_v_neg_sampling(self, count):
        neg_v = numpy.random.choice(self.sample_table, size=(count)).tolist()
        
        #convert list to string with tab separator
        temp = neg_v
        neg_v = "\t".join([str(t) for t in temp])
        return neg_v
   

    def makeTriplesetsFromFile(self,k=5):
        
        #Remove the file if it already exists
        try:
            os.remove(self.posfile)
        except:
            pass
        
        #Remove the file if it already exists
        try:
            os.remove(self.negfile)
        except:
            pass
        
        #Remove the file if it already exists
        try:
            os.remove(self.statfile)
        except:
            pass
            
        dataset_size = 0
        
        posOutputFile = open(self.posfile, "a")
        negOutputFile = open(self.negfile, "a")
        
        with open(self.initial_data_sets_file,"r") as iDSFile:
        
            for triple in iDSFile:
                
                dataset = triple.strip('\n').split(':')
                
                wid1 = int(dataset[0])
                wid2 = int(dataset[1])
                iwid = int(dataset[2])
            
                pair = (wid1,wid2)
            
                if pair in self.pair2id:
                    pid = self.pair2id[pair]
                    
                    output = str(pid)+"\t"+str(iwid)
                    posOutputFile.write(output+"\n")

                    #for every positive sample, create 'k' negative samples from unigram noise ditribution
                    neg_v = self.get_neg_v_neg_sampling(k)
                    
                    output = neg_v
                    negOutputFile.write(str(output)+"\n")

                    dataset_size += 1
        
        
        posOutputFile.close()
        negOutputFile.close()
        os.remove(self.outputfolder+'/InitialDatasets')
        
        
        with open(self.statfile,"a") as statFile:
            statFile.write("Dataset :"+str(dataset_size))
            
if __name__ ==  '__main__':
    
    inputfolder = sys.argv[1]
    outputfolder = sys.argv[2]
    windowSize = int(sys.argv[3])
    minWordCount = int(sys.argv[4]) #eg: 700 thresholds value for word count
    minPairCount = int(sys.argv[5]) #eg: 200 thresholds value for pair count
    k = 5 #k values for negative sampling

    data = Datasets(inputfolder, outputfolder, windowSize, minWordCount, minPairCount)
    #print(cProfile.runctx('data.makeTriplesets(k)',globals(),locals()))
    ###
    data.makeTriplesetsFromFile(k)
    ###

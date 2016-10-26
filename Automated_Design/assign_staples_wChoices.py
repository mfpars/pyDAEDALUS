from math import floor

from Automated_Design.util import intersect_lists, find


def generate_spanning_21_bp_staples(num_21_staps, scaf_bot_cut,
                                    scaf_top_cut):
    staple_list = []
    for i in range(num_21_staps):
        a = (21 * i)
        a = a if a > 0 else None  # because reversing the order of slicing and saying "go till 0" means to "go until just before 0".  To actually go to index 0, you need to not pass in a value into the 'end' part of slicing or equivalently pass in None.  #TODO: test when `a` doesn't equal 0
        b = 21 * (i + 1)
        temp_stap = scaf_bot_cut[a:b] + scaf_top_cut[b-1:a:-1]
        # Adjust nick to center on bottom strand (5' 10 21 11 3' split)
        reordered_temp_stap = temp_stap[11:] + temp_stap[0:11]
        staple_list.append(reordered_temp_stap)
    return staple_list



def assign_staples_wChoices(edges, num_edges, edge_type_mat, scaf_to_edge, num_bases, num_vert, singleXOs):
    """
    Assign staples to edges following prescribed patterns
    Inputs: edges = Ex2 matrix where each row corresponds to one edge,
              denoting the vertices being connected. 1st column > 2nd column
            num_edges = number of edges, E
            edge_type_mat = VxV sparse matrix (V = number of vertices) where
      1 is non-spanning tree edge: DX edge with 1 scaffold crossover
      2 is spanning tree edge: DX edge with 0 scaffold crossovers
            scaf_to_edge = Ex2 cell array, where each row corresponds to one
               edge, 1st column is duplex from low ID to high ID vertex,
               2nd column is from high to low. Each element is a row vector
               containing the scaffold base IDs in order on that duplex.
            scaf_nick_pos = number of bases upstream of scaffold nick
            num_bases = number of bases of scaffold in structure
            num_vert = number of vertices, V
            singleXOs = 1 if using vertex staples with single crossovers,
               0 if not.
Output: staples = cell array with E rows, each cell contains row vector.
        Some cells may be empty as fragments are combined into full staples.
        Columns 0-3 contain vertex staples, while 4+ contain edge staples.
    ##########################################################################
    by Sakul Ratanalert, MIT, Bathe Lab, 2016

    Copyright 2016. Massachusetts Institute of Technology. Rights Reserved.
    M.I.T. hereby makes following copyrightable material available to the
    public under GNU General Public License, version 2 (GPL-2.0). A copy of
    this license is available at https://opensource.org/licenses/GPL-2.0
    ##########################################################################
    """

    staples = [[None]*4 for i in range(num_edges)] # minimum two staples per edge
    end = -1 #TODO:  UUUUUUGHGRFFFF.  This varaible should be gone.

    didit = False  #TODO: for debugging.  Remove.

    for edge_ID in range(num_edges):
        edge_bgn = edges[edge_ID][1] # lower on left
        edge_fin = edges[edge_ID][0] # higher on right

        scaf_1 = scaf_to_edge[edge_ID][0] # low to high 5' to 3'
        scaf_2 = scaf_to_edge[edge_ID][1] # high to low 5' to 3'

        edge_type = edge_type_mat[edge_bgn][edge_fin]['type']

        scaf_top = scaf_1 # low to high 5' to 3'
        scaf_bot = scaf_2[end::-1] # low to high 3' to 5'

        # # Fragments 0-3 form vertex staples. 0 and 1 connect to 2 and 3 on
        # # other edges.
        if singleXOs: # singleXOs on  #! if single crossovers are on, then will have a pattern that makes breakpoint of staple be at crossover.

            #TODO: remove staples 1 and 4.  change init'd stap_ID to 4.
            staples[edge_ID][0] = scaf_bot[0:10] # 5 bp -> 10
            staples[edge_ID][1] = scaf_top[10::-1] # 6 bp -> 11
            staples[edge_ID][2] = scaf_top[end:end-10:-1] # 5 bp -> 10
            staples[edge_ID][3] = scaf_bot[-11:] # 6 bp -> 11

        else: # singleXOs off, doubleXOs instead
            #TODO:
            raise Exception("Section not tested")

            staples[edge_ID][0] = scaf_bot[0:10] + scaf_top[11:5:-1] # 10+6 bp
            staples[edge_ID][1] = scaf_top[5::-1] # 5 bp
            staples[edge_ID][2] = scaf_top[end:end-10:-1] + scaf_bot[end-11+1:end-5] # 10+6 bp
            staples[edge_ID][3] = scaf_bot[-5:] # 5 bp



        # # Begin adding edge staples
        stap_ID = 4 # initialize staple ID

        # # Clip off ends that bind to vertex staple
        scaf_top_cut = scaf_top[11:-10]
        scaf_bot_cut = scaf_bot[10:-11]

        len_cut = len(scaf_top_cut) # length requiring edge staples

        if len_cut > 0: # if there are any other staples to be added
            if edge_type == 2: # tree edge, no scaffold crossover
                num_21staps = int(floor(len_cut/21)) # number of 21x2-nt staples
                len_extra_stap = int(len_cut - 21*num_21staps) # remaining staple, 10x2 or 11x2

                # # Add the staples that span 21 bp
                bp_staples = generate_spanning_21_bp_staples(num_21staps,
                                                             scaf_bot_cut,
                                                             scaf_top_cut)
                staples[edge_ID] += bp_staples
                stap_ID += 1

                # # Add the extra staple if necessary
                # # abutting the higher index vertex
                if len_extra_stap > 0: # if an extra staple is required
                    temp_stap = scaf_bot_cut[end-len_extra_stap+1:] + scaf_top_cut[end:end-len_extra_stap:-1]
                    staples[edge_ID].append(temp_stap)
                    stap_ID += 1  # at this point, stap_ID doesn't matter.  but for consistency..   #TODO: Can I remove stap_ID?


            else: # nontree edge, 1 scaffold crossover

                num_21staps = floor(len_cut/21) # number of 21x2-nt staples

                # Going to match Table S1 to find what X and Y are.
                #TODO: also done in enum_scaff_bases.  Extract both as function
                # # Detect scaffold crossover location
                if len_cut == 21*num_21staps: # scaffold crossover 5/6 away from center
                    if len_cut % 2 == 0: # even
                        cutoff = int(len_cut / 2 - 5)
                    else: # odd
                        cutoff = int(len_cut / 2 - 5.5)
                else: # scaffold crossover 0/1 away from center
                    if len_cut % 2 == 0: # even
                        cutoff = int(len_cut / 2)
                    else: # odd
                        cutoff = int(len_cut / 2 - 0.5)

                cutoff += 1 # cutoff is currently last number on left, but
                # slicing notation takes everything less than given number.

                # # Split top scaffold strand in two
                scaf_top_cut_left = scaf_top_cut[:cutoff]
                scaf_top_cut_rght = scaf_top_cut[cutoff:]

                # # Split bottom scaffold strand in two
                scaf_bot_cut_left = scaf_bot_cut[:cutoff]
                scaf_bot_cut_rght = scaf_bot_cut[cutoff:]

                # # Check if 15/16 or 16/16 scaffold crossover staple
                len_left = len(scaf_top_cut_left)  ## Basically X
                len_rght = len(scaf_top_cut_rght)  ## basically Y

                rem_left = len_left % 21
                rem_rght = len_rght % 21


                if rem_left == 15:
                    left_SCS = min(15, len_left)  # scs = scaffold crossover staple
                else: # 5/26, 6/27, 16
                    left_SCS = min(16, len_left)

                if rem_rght == 15:
                    rght_SCS = min(15, len_rght)
                else: # 5/26, 6/27, 16
                    rght_SCS = min(16, len_rght)


                # # Define new regions
                # # Region with staples that cross scaffold crossovers
                scaf_top_SCS = scaf_top_cut_left[-left_SCS:] + scaf_top_cut_rght[:rght_SCS]
                scaf_bot_SCS = scaf_bot_cut_left[-left_SCS:] + scaf_bot_cut_rght[:rght_SCS]


                # # Regions to the left and right of the scaf crossover staples
                scaf_top_cut_left_noSCS = scaf_top_cut_left[:end-left_SCS]
                scaf_top_cut_rght_noSCS = scaf_top_cut_rght[rght_SCS+1:]
                len_left_noSCS = len(scaf_top_cut_left_noSCS)
                len_rght_noSCS = len(scaf_top_cut_rght_noSCS)

                scaf_bot_cut_left_noSCS = scaf_bot_cut_left[:end-left_SCS]
                scaf_bot_cut_rght_noSCS = scaf_bot_cut_rght[rght_SCS+1:]

                if scaf_top_cut_left_noSCS:
                    raise Exception("Test")
                if scaf_top_cut_rght_noSCS:
                    raise Exception("Test")
                if scaf_bot_cut_left_noSCS:
                    raise Exception("Test")
                if scaf_bot_cut_rght_noSCS:
                    raise Exception("Test")

                if len_cut <= 11:
                    # # if len_cut <= 11, make single-crossover edge staple
                    staples[edge_ID].append(scaf_bot_SCS)
                    stap_ID += 1
                    staples[edge_ID].append(scaf_top_SCS[end::-1])
                    stap_ID += 1
                else:
                    # # Do SCStaples, nick 8 bp away from 3'   ##!! should match the picture.
                    staples[edge_ID].append(scaf_bot_SCS[-8:] + scaf_top_SCS[end:8-1:-1])
                    stap_ID += 1
                    staples[edge_ID].append(scaf_top_SCS[8-1::-1] + scaf_bot_SCS[:-8])
                    stap_ID += 1


                if len_cut <= 21: # total length 42 or less, merge staples  ##!! Then to seperate check to see if you merge them
                    raise Exception("Test")
                    staples[edge_ID][stap_ID-2] = staples[edge_ID][stap_ID-2] + staples[edge_ID][stap_ID-1]
                    staples[edge_ID][stap_ID-1] = []


                # # Do LEFT of SCS
                num_21staps = int(floor(len_left_noSCS/21))
                len_extra_stap = len_left_noSCS - 21*num_21staps

                # # Add the extra staple if necessary, should go closest to vertex
                if len_extra_stap > 0: # if an extra staple is required
                    raise Exception("Test")
                    temp_stap = scaf_top_cut_left_noSCS[len_extra_stap:1:-1] + scaf_bot_cut_left_noSCS[1:len_extra_stap]
                    staples[edge_ID][stap_ID] = temp_stap
                    stap_ID = stap_ID + 1 # increment staple ID

                    # # Cut out this region
                    scaf_top_cut_left_noSCS = scaf_top_cut_left_noSCS[len_extra_stap+1:end]
                    scaf_bot_cut_left_noSCS = scaf_bot_cut_left_noSCS[len_extra_stap+1:end]


                # # Add the staples that span 21 bp
                staples[edge_ID] += generate_spanning_21_bp_staples(
                    num_21staps, scaf_bot_cut_left_noSCS,
                    scaf_top_cut_left_noSCS)

                # # Do RIGHT of SCS
                num_21staps = int(floor(len_rght_noSCS/21))
                len_extra_stap = len_rght_noSCS - 21*num_21staps

                # # Add the staples that span 21 bp
                staples[edge_ID] += generate_spanning_21_bp_staples(
                    num_21staps, scaf_bot_cut_rght_noSCS,
                    scaf_top_cut_rght_noSCS)


                # # Add the extra staple if necessary, should go closest to vertex  ##!! add staple at end instead of beginning
                if len_extra_stap > 0: # if an extra staple is required
                    raise Exception("Test")
                    temp_stap = scaf_bot_cut_rght_noSCS[len_extra_stap:] + scaf_top_cut_rght_noSCS[-1:len_extra_stap:-1]
                    staples[edge_ID].append(temp_stap)


    # # Add polyTs after all preliminary staples generated
    len_polyT = 5

    # # Join 11 and 10 staples with polyT to make 11+5+10 = 26 nt fragments
    for edge_ID in range(len(staples)):
        for elev_Vstap_ID in [1, 3]: # len 11 staples
            this_eleven_Vstap = staples[edge_ID][elev_Vstap_ID]
            three_prime_end = this_eleven_Vstap[-1]
            for other_edge_ID in range(num_edges):
                for ten_Vstap_ID in [0, 2]: # len 10 staples
                    this_ten_Vstaple = staples[other_edge_ID][ten_Vstap_ID]
                    if this_ten_Vstaple: # if it is not empty
                        five_prime_end = this_ten_Vstaple[0]
                        # print '-----'
                        # print type(five_prime_end), five_prime_end
                        # if five_prime_end == 450:
                        #     import ipdb; ipdb.set_trace()
                        # print type(three_prime_end), three_prime_end
                        thing = int(three_prime_end) - int(five_prime_end)  #TODO: Change datatype test data is read in as?  Occasionally getting overflow errors here without surrounding `int()`s.
                        they_are_consecutive = (thing) == 1
                        they_wrap_around = (three_prime_end == 0) and five_prime_end == (num_bases - 1)
                        if they_are_consecutive or they_wrap_around:
                            # # Concatenate with len_polyT zeros in between
                            staples[edge_ID][elev_Vstap_ID] = this_eleven_Vstap + ([-1]*len_polyT) + this_ten_Vstaple

                            # # Change five_prime_end staple to indicate where
                            # # piece went, using - to make it not a real ID
                            staples[other_edge_ID][ten_Vstap_ID] = [-edge_ID, -elev_Vstap_ID]


    # # Group vertex staple fragments int 52 nt (4 domains) and 78 nt (6 domains) staples
    for vert_ID in range(num_vert):
        neighbors = edge_type_mat.neighbors(vert_ID)
        degree = len(neighbors) # degree of vertex
        num_four_dom_Vstap = -degree % 3 # num of 26x2 = 52 nt staples, has 4 domains
        num_six_dom_Vstap = (degree - 2*num_four_dom_Vstap)/3 # num of 26x3 = 78 nt staples, has 6 domains

        # # Identify starting position of routing
        # identify all neighbor ids that are greater than vert_ID:
        bigger_neighbors = [neighbor for neighbor in neighbors if neighbor > vert_ID]

        if len(bigger_neighbors) == 0:
            start_vert = min(neighbors) # this one WILL HAVE a single-crossover
        else:
            start_vert = min(bigger_neighbors) # this one WILL HAVE a single-crossover

        # # Find starting position
        if vert_ID > start_vert:
            start_edge_ID = find(edges, [vert_ID, start_vert])[0]
            start_Vstap_ID = 3 # right vertex
        else:
            start_edge_ID = find(edges, [start_vert, vert_ID])[0]
            start_Vstap_ID = 1 # left vertex

        # # Find edge with the fragment from start_edge
        next_edge_ID = staples[start_edge_ID][start_Vstap_ID-1][0]*-1
        next_Vstap_ID = staples[start_edge_ID][start_Vstap_ID-1][1]*-1

        # # Obtain next edge to visit
        edge_ID = next_edge_ID
        Vstap_ID = next_Vstap_ID

        start_edge_ID = edge_ID
        start_Vstap_ID = Vstap_ID


        #TODO: There has to be a way to clean up these next two loops...
        for staple_ID in range(num_six_dom_Vstap):

            # # Domains 5 and 6
            five_six = staples[start_edge_ID][start_Vstap_ID]
            staples[start_edge_ID][start_Vstap_ID] = [] # clear once stored

            next_edge_ID = staples[edge_ID][Vstap_ID-1][0]*-1
            next_Vstap_ID = staples[edge_ID][Vstap_ID-1][1]*-1
            staples[edge_ID][Vstap_ID-1] = [] # clear once stored

            # # Obtain next edge to visit
            edge_ID = next_edge_ID
            Vstap_ID = next_Vstap_ID

            # # Domains 3 and 4
            three_four = staples[edge_ID][Vstap_ID]
            staples[edge_ID][Vstap_ID] = [] # clear once stored

            next_edge_ID = staples[edge_ID][Vstap_ID-1][0]*-1
            next_Vstap_ID = staples[edge_ID][Vstap_ID-1][1]*-1
            staples[edge_ID][Vstap_ID-1] = [] # clear once stored

            # # Obtain next edge to visit
            edge_ID = next_edge_ID
            Vstap_ID = next_Vstap_ID

            # # Domains 1 and 2
            one_two = staples[edge_ID][Vstap_ID]
            staples[edge_ID][Vstap_ID] = [] # clear once stored

            next_edge_ID = staples[edge_ID][Vstap_ID-1][0]*-1
            next_Vstap_ID = staples[edge_ID][Vstap_ID-1][1]*-1

            # # Concatenate together
            staples[edge_ID][Vstap_ID] = one_two + three_four + five_six

            # # Obtain next edge to visit
            edge_ID = next_edge_ID
            Vstap_ID = next_Vstap_ID

            # # Reset new start
            start_edge_ID = edge_ID
            start_Vstap_ID = Vstap_ID


        for staple_ID in range(num_four_dom_Vstap):

            # # Domains 3 and 4
            three_four = staples[start_edge_ID][start_Vstap_ID]
            staples[start_edge_ID][start_Vstap_ID] = [] # clear once stored

            next_edge_ID = staples[edge_ID][Vstap_ID-1][0]*-1
            next_Vstap_ID = staples[edge_ID][Vstap_ID-1][1]*-1
            staples[edge_ID][Vstap_ID-1] = [] # clear once stored

            # # Obtain next edge to visit
            edge_ID = next_edge_ID
            Vstap_ID = next_Vstap_ID

            # # Domains 1 and 2
            one_two = staples[edge_ID][Vstap_ID]
            staples[edge_ID][Vstap_ID] = [] # clear once stored

            next_edge_ID = staples[edge_ID][Vstap_ID-1][0]*-1
            next_Vstap_ID = staples[edge_ID][Vstap_ID-1][1]*-1

            # # Concatenate together
            staples[edge_ID][Vstap_ID] = one_two  +three_four

            # # Obtain next edge to visit
            edge_ID = next_edge_ID
            Vstap_ID = next_Vstap_ID

            # # Reset new start
            start_edge_ID = edge_ID
            start_Vstap_ID = Vstap_ID



    # # Clean up remaining Vstap fragments
    for edge_ID in range(num_edges):
        for ten_Vstap_ID in [0, 2]: # "len 10 staples," actually just indicators
            staples[edge_ID][ten_Vstap_ID] = [] # clear

    return staples
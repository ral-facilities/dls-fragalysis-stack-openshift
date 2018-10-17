#!/usr/bin/env python

"""process_molport_vendor.py

Processes MolPort vendor files, expected to contain pricing information.
Four new files are generated and the original nodes file augmented with
a "V_MP" label.

The files generated are:

-   "cost_nodes.csv.gz"
    containing nodes that define the unique set of costs.

-   "vendor_nodes.csv.gz"
    containing all the nodes for the vendor compounds
    (that have at least one set of pricing information).

-   "vendor_cost_relationships.csv.gz"
    containing the "Vendor" to "Cost"
    relationships using the the type of "COSTS".

-   "molecule_vendor_relationships.csv.gz"
    containing the relationships between the original node entries and
    the "Vendor" nodes. There is a relationship for every MolPort
    compound that was found in the earlier processing.

The module also augments the original nodes by adding the label
"V_MP".

Alan Christie
October 2018
"""

import argparse
from collections import namedtuple
import glob
import gzip
import os
import re

# MolPort Columns (tab-separated)
#
# SMILES                0
# SMILES_CANONICAL      1
# MOLPORTID             2
# STANDARD_INCHI        3
# INCHIKEY              4
# PRICERANGE_1MG        5
# PRICERANGE_5MG        6
# PRICERANGE_50MG       7
# BEST_LEAD_TIME        8

# The Vendor node has...
# a UUID
# a compound id
# a smiles string
# a best lead time
VendorNode = namedtuple('VendorNode', 'uuid c s blt')
# The Cost node has...
# a unique id (assigned after collection)
# a pack size
# a minimum price
# a maximum price
CostNode = namedtuple('CostNode', 'ps min max')
# A unique set of cost nodes
cost_nodes = set()
# The set of Vendor nodes (and a list of their cost nodes)
vendor_map = {}
# The vendor compound IDs that have pricing information
costed_vendor_map = {}

# Prefixes for the vendor and cost node IDs.
vendor_uuid_prefix = 'vnm'
cost_uuid_prefix = 'cnm'
# Prefix for output files
output_filename_prefix = 'molport'

# The next unique ID for a vendor node.
next_vendor_id = 1

# Regular expression to find
# MolPort compound IDs in the original nodes file.
molport_re = re.compile(r'MolPort:(\d+-\d+-\d+)[^\d]')

# Various diagnostic counts
num_compounds_without_costs = 0
num_vendor_cost_relationships = 0
num_nodes = 0
num_nodes_augmented = 0
num_vendor_relationships = 0


def create_cost_node(pack_size, field_value):
    """Creates a CostNode namedtuple for the provided pack size
    and corresponding pricing field. The pricing field
    may be empty.

    :param pack_size: The pack size (mg). Typically 1, 5, 50 etc.
    :param field_value: The pricing field value, e.g. '100 - 500'
    :returns: A CostNode namedtuple (or None if no pricing). The global
              set (cost_nodes) is also added to.
    """

    global cost_nodes

    # The cost/pricing field value
    # has a value that is one of:
    #
    # "min - max"
    # "< max"
    # "> min"

    min_val = None
    max_val = None
    c_node = None
    if field_value.startswith('>'):
        min_val = float(field_value.split()[1])
    elif field_value.startswith('<'):
        max_val = float(field_value.split()[1])
    elif ' - ' in field_value:
        min_val = float(field_value.split(' - ')[0])
        max_val = float(field_value.split(' - ')[1])

    if min_val or max_val:
        c_node = CostNode(pack_size, min_val, max_val)
        cost_nodes.add(c_node)

    return c_node


def extract_costs(gzip_filename):
    """Process the given file and extract vendor and pricing information.
    Vendor nodes are only created when there is at least one
    column of pricing information.
    """

    global vendor_map
    global costed_vendor_map
    global next_vendor_id
    global num_compounds_without_costs

    print('Processing {}...'.format(gzip_filename))

    num_lines = 0
    with gzip.open(gzip_filename, 'rt') as gzip_file:

        # Dump first line (header)
        hdr = gzip_file.readline()

        for line in gzip_file:

            num_lines += 1
            fields = line.split('\t')

            smiles = fields[0]
            compound_id = fields[2].split('MolPort-')[1]
            blt = int(fields[8].strip())
            vendor_node = VendorNode(next_vendor_id, compound_id, smiles, blt)
            next_vendor_id += 1

            cost_node_1 = create_cost_node(1, fields[5])
            cost_node_5 = create_cost_node(5, fields[5])
            cost_node_50 = create_cost_node(50, fields[5])

            costs = []
            if cost_node_1:
                costs.append(cost_node_1)
            if cost_node_5:
                costs.append(cost_node_5)
            if cost_node_50:
                costs.append(cost_node_50)
            if costs:
                vendor_map[vendor_node] = costs
                costed_vendor_map[compound_id] = vendor_node
            else:
                num_compounds_without_costs += 1


def write_cost_nodes(directory, cost_map):
    """Writes the CostNodes to a node file, including a header.
    """

    filename = os.path.join(directory,
                            '{}_cost_nodes.csv.gz'.format(output_filename_prefix))
    print('Writing {}...'.format(filename))

    with gzip.open(filename, 'wb') as gzip_file:
        gzip_file.write(':ID,'
                        'currency,'
                        'pack_size:INT,'
                        'min_price:FLOAT,'
                        'max_price:FLOAT,'
                        ':LABEL\n')
        for cost in cost_map:
            min = ''
            if cost.min:
                min = cost_node.min
            max = ''
            if cost.max:
                max = cost_node.max
            uuid = cost_map[cost_node]
            gzip_file.write('{}{},USD,{},{},{},Cost\n'.format(cost_uuid_prefix,
                                                              uuid,
                                                              cost.ps,
                                                              min,
                                                              max))


def write_vendor_nodes(directory, vendor_map):
    """Writes the VendorNodes to a node file, including a header.
    """

    filename = os.path.join(directory,
                            '{}_vendor_nodes.csv.gz'.format(output_filename_prefix))
    print('Writing {}...'.format(filename))

    with gzip.open(filename, 'wb') as gzip_file:
        gzip_file.write(':ID,'
                        'vendor,'
                        'cmpd_id,'
                        'smiles,'
                        'best_lead_time:INT,'
                        ':LABEL\n')
        for vendor in vendor_map:
            gzip_file.write(
                '{}{},{},{},{},{},Vendor\n'.format(vendor_uuid_prefix,
                                                   vendor.uuid,
                                                   "MolPort",
                                                   vendor.c,
                                                   vendor.s,
                                                   vendor.blt))


def write_vendor_cost_relationships(directory, vendor_map, cost_map):
    """Writes the Vendor to Costs relationships.
    """

    global num_vendor_cost_relationships

    filename = os.path.join(directory,
                            '{}_vendor_cost_relationships.csv.gz'.format(output_filename_prefix))
    print('Writing {}...'.format(filename))

    with gzip.open(filename, 'wb') as gzip_file:
        gzip_file.write(':START_ID,'
                        ':END_ID,'
                        ':TYPE\n')
        for vendor in vendor_map:
            # Generate a relationship for each cost.
            # The source is the vendor UUID (with a prefix)
            # and the destination is the Code UUID (with a prefix)
            for cost in vendor_map[vendor]:
                if cost:
                    cost_uuid = cost_map[cost]
                    gzip_file.write(
                        '{}{},{}{},COSTS\n'.format(vendor_uuid_prefix,
                                                   vendor.uuid,
                                                   cost_uuid_prefix,
                                                   cost_uuid))
                    num_vendor_cost_relationships += 1
                else:
                    print(' No cost node for {}'.format(vendor.c))


def augment_original_nodes(directory, filename, has_header):
    """Augments the original nodes file and writes the relationships
    for nodes in this file to the Vendor nodes.
    """

    global num_nodes
    global num_nodes_augmented
    global num_vendor_relationships

    print('Augmenting {} as...'.format(filename))

    # Augmented file
    augmented_filename = \
        os.path.join(directory,
                     '{}_augmented_{}'.format(output_filename_prefix,
                                              os.path.basename(filename)))
    gzip_ai_file = gzip.open(augmented_filename, 'wt')
    # Frag to Vendor Compound relationships file
    augmented_relationships_filename = \
        os.path.join(directory,
                     '{}_molecule_vendor_relationships.csv.gz'.format(output_filename_prefix))
    gzip_cr_file = gzip.open(augmented_relationships_filename, 'wt')
    gzip_cr_file.write(':START_ID,'
                       ':END_ID,'
                       ':TYPE\n')

    print(' {}'.format(augmented_filename))
    print(' {}'.format(augmented_relationships_filename))

    with gzip.open(filename, 'rt') as gzip_i_file:

        if has_header:
            # Copy first line (header)
            hdr = gzip_i_file.readline()
            gzip_ai_file.write(hdr)

        for line in gzip_i_file:

            num_nodes += 1
            # Search for a potential MolPort identity
            # Get the MolPort compound
            # if we know the compound add a label
            augmented = False
            match_ob = molport_re.findall(line)
            if match_ob:
                # Look for compounds where we have a costed vendor.
                # If there is one, add the "V_MP" label.
                for compound_id in match_ob:
                    if compound_id in costed_vendor_map:
                        new_line = line.strip() + ';V_MP\n'
                        gzip_ai_file.write(new_line)
                        augmented = True
                        num_nodes_augmented += 1
                        break
                if augmented:
                    # If we've augmented the line
                    # append a relationship to the relationships file
                    # for each compound that was found...
                    for compound_id in match_ob:
                        if compound_id in costed_vendor_map:
                            # Now add vendor relationships to this row
                            frag_id = line.split(',')[0]
                            gzip_cr_file.write('{},{}{},HAS_VENDOR\n'.format(frag_id,
                                                                             vendor_uuid_prefix,
                                                                             costed_vendor_map[compound_id].uuid))
                            num_vendor_relationships += 1

            if not augmented:
                # No vendor for this line,
                # just write it out 'as-is'
                gzip_ai_file.write(line)

    # Close augmented nodes and the relationships
    gzip_ai_file.close()
    gzip_cr_file.close()


if __name__ == '__main__':

    parser = argparse.ArgumentParser('Vendor Processor (MolPort)')
    parser.add_argument('dir',
                        help='The MolPort vendor directory,'
                             ' containing the ".gz" files to be processed.'
                             ' All the ".gz" files in the supplied directory'
                             ' will be inspected.')
    parser.add_argument('nodes',
                        help='The nodes file to augment with the collected'
                             ' vendor data')
    parser.add_argument('output',
                        help='The output directory')
    parser.add_argument('--nodes-has-header',
                        help='Use if the nodes file has a header',
                        action='store_true')

    args = parser.parse_args()

    # Create the output directory
    if not os.path.exists(args.output):
        os.mkdir(args.output)
    if not os.path.isdir(args.output):
        print('ERROR: output ({}) is not a directory'.format(args.output))
        sys.exit(1)

    # Process all the files...
    molport_files = glob.glob('{}/*.gz'.format(args.dir))
    for molport_file in molport_files:
        extract_costs(molport_file)

    # Assign unique identities to the collected Cost nodes
    # using a map of cost node against the assigned ID.
    # We have to do this now because namedtuples are immutable,
    # so we collect Cost nodes first and then create unique IDs.
    cost_map = {}
    next_cost_node_uuid = 1
    for cost_node in cost_nodes:
        cost_map[cost_node] = '{}'.format(next_cost_node_uuid)
        next_cost_node_uuid += 1

    # Write the new nodes and relationships
    # and augment the original nodes file.
    if cost_map:
        write_cost_nodes(args.output, cost_map)
        write_vendor_nodes(args.output, vendor_map)
        write_vendor_cost_relationships(args.output, vendor_map, cost_map)
        augment_original_nodes(args.output, args.nodes, has_header=args.nodes_has_header)

    # Summary
    print('{} costs'.format(len(cost_map)))
    print('{} vendor compounds with costs'.format(len(vendor_map)))
    print('{} vendor compounds without any costs'.format(num_compounds_without_costs))
    print('{} vendor compound cost relationships'.format(num_vendor_cost_relationships))
    print('{} nodes'.format(num_nodes))
    print('{} augmented nodes'.format(num_nodes_augmented))
    print('{} node vendor relationships'.format(num_vendor_relationships))
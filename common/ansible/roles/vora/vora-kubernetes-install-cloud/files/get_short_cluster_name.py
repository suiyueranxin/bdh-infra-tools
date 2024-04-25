import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Lost of cluster name in parameters"
        exit(1)
    cluster_name = sys.argv[1]
    if len(cluster_name) < 19 or len(cluster_name.split('-')) < 3:
        print "Incorrect cluster name format! It should be as email-20180427-102353996"
        exit(1)

    print cluster_name[:-18] + cluster_name[-7:]

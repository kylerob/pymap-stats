import imaplib
import email
import pprint
import time
import operator
import getpass
import argparse
import os

parser = argparse.ArgumentParser("Get stats about the emails you receive, your usage, etc.")
parser.add_argument("-n", "--num_emails", type=int, help="The number of emails to pull from the email address. Leave off argument for all.")
parser.add_argument("-s", "--server", help="The IMAP server to connect to (defaults to imap.gmail.com).", default="imap.gmail.com") 
parser.add_argument("-p", "--persist", action="store_true", help="Use to persist emails for later analysis. Will speed up future runs by avoiding calls to the IMAP server.")
args = parser.parse_args()

# TODO: check for valid --num_emails
# TODO: check for valid --server
# TODO: use persist flag to store emails in local file system, maybe get number of files and estimated space to give [Y/n]
# TODO: catch imap server unknown error

imap_server = args.server
username = raw_input("Email address: ")
password = getpass.getpass()

save_path = None
prog_dir = "mail_stats"
email_dir = "emails"
home_dir = None
if args.persist:
	home_dir = os.path.expanduser("~") 
	print "Using %s/%s/%s to save files." % (home_dir, prog_dir, email_dir)
	save_path = "%s/%s/%s" % (home_dir, prog_dir, email_dir)
	if not os.path.isdir(save_path):
		os.makedirs(save_path)

def print_top_from(from_dict, num=10):
	print "Top received emails:\n"
	for i, (k,v) in enumerate(from_dict):
		if i < (num): 
			print "%d. %s (%s times)" % (i+1,k,v)
		else: 
			break

def write_all_from(from_dict):
	with open("from.txt", "w") as from_file:
		for i,(k,v) in enumerate(from_dict):
			from_file.write("%d. %s (%s times)\n" % (i+1,k,v))

def connect(retries=5, delay=3):
    while True:
        try:
            # imap_server = 'imap.gmail.com'
            mail = imaplib.IMAP4_SSL(imap_server)
            mail.login(username, password)
            return mail
        except imaplib.IMAP4_SSL.abort:
            if retries > 0:
                retries -= 1
                time.sleep(delay)
            else:
                raise

# check for home_dir directory 
# create if not available


start_millis = int(round(time.time() * 1000))

mail = connect()
sorted_from_dict = {}
while True:
	try:
		mail.select("INBOX", True)
		result, data = mail.uid("search", None, "ALL")
		mail_ids = data[0].split()[:]

		print(args.num_emails)
		num_retrieve = args.num_emails or len(mail_ids)
		print(num_retrieve)

		mail_ids = data[0].split()[:num_retrieve]

		from_dict = {}

		for mail_id in mail_ids:
			print "Mail id: %s" % mail_id

			if args.persist:
				filename = "%s.txt" % mail_id
				file_path = save_path + "/" + filename
				if os.path.exists(file_path):
					with open(file_path, 'r') as email_file:
						raw_email = email_file.read()
			else:
				result, email_pieces = mail.uid('fetch', mail_id, '(RFC822)')
				# pp = pprint.PrettyPrinter(indent=4)
				# pp.pprint(email_pieces)
				raw_email = email_pieces[0][1]
			
			parsed_message = email.message_from_string(raw_email)

			if args.persist:
				with open(file_path, 'w') as email_file:
					email_file.write(raw_email)

			email_from = parsed_message["From"]
			email_to = parsed_message["To"]
			print email_to

			# print "Sender: %s" % parsed_message["Sender"]
			# print "From: %s" % email_from

			email_from_tuple = email.utils.parseaddr(email_from)
			parsed_from_addr = ""
			if email_from_tuple[1]:
				parsed_from_addr = email_from_tuple[1]
				if parsed_from_addr in from_dict:
					from_dict[parsed_from_addr] += 1
				else:
					from_dict[parsed_from_addr] = 1


		sorted_from_dict = sorted(from_dict.iteritems(), key=operator.itemgetter(1), reverse=True)
		print sorted_from_dict

		print_top_from(sorted_from_dict)

		end_millis = int(round(time.time() * 1000))
		print end_millis - start_millis
		# we're done, exit while loop
		break
	except Exception, e:
		print e
		mail = connect()

write_all_from(sorted_from_dict)


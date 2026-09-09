/*
 * fileio.c
 *
 * (c) 2015 SIP-Online
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 *
 */

#include "e2_procfs.h"
#include <linux/namei.h>
#include <linux/version.h>

struct file* file_open(const char* path, int flags, int rights) {
	struct file* filp = NULL;
	int err = 0;

	filp = filp_open(path, flags, rights);

	if (IS_ERR(filp))
	{
		err = PTR_ERR(filp);
		return NULL;
	}

	return filp;
}

void file_close(struct file* file)
{
	if (file != NULL)
	{
		filp_close(file, NULL);
	}
}

int file_read(struct file* file, unsigned char* data, unsigned int size)
{
	int ret;

	ret = kernel_read(file, data, size, &file->f_pos);

	return ret;
}

int file_write(struct file* file, unsigned char* data, unsigned int size)
{
	int ret;

	ret = kernel_write(file, data, size, &file->f_pos);

	return ret;
}

int remove_file(char *path)
{
	int ret;
	struct path ndpath;
	struct dentry *dentry;

	ret = kern_path(path, LOOKUP_PARENT, &ndpath);
	if (ret != 0)
	{
		return -ENOENT;
	}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(6, 16, 0)
	/* В новых ядрах lookup_one_len была заменена на работу через struct qstr */
	struct qstr q = QSTR_INIT(path, strlen(path));
	/* Используем unlocked-версию, так как родительский семафор i_rwsem не залочен */
	dentry = lookup_noperm_unlocked(&q, ndpath.dentry);
#else
	dentry = lookup_one_len(path, ndpath.dentry, strlen(path));
#endif

	if (IS_ERR(dentry))
	{
		path_put(&ndpath);
		return -EACCES;
	}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 12, 0)
	/* Современная vfs_unlink требует передавать idmap (в большинстве случаев &nop_mnt_idmap) */
	vfs_unlink(&nop_mnt_idmap, d_inode(ndpath.dentry), dentry, NULL);
#else
	vfs_unlink(ndpath.dentry->d_inode, dentry, NULL);
#endif

	dput(dentry);
	path_put(&ndpath); // Освобождаем path, полученный из kern_path

	return ret;
}

int save_data_to_file(char *path, int flags, char *data, int size)
{
	struct file *fp = NULL;

	fp = file_open(path, flags, 0);
	if (fp != NULL)
	{
		file_write(fp, data, size);
		file_close(fp);

		return 0;
	}

	return -1;
}

/* the function returns the directry name */
char * dirname(char * name)
{
	static char path[100];
	int i = 0;
	int pos = 0;

	while ((name[i] != 0) && (i < sizeof(path)))
	{
		if (name[i] == '/')
			pos = i;

		path[i] = name[i];
		i++;
	}

	path[i] = 0;
	path[pos] = 0;

	return path;
}

/* the function returns the base name */
char * basename(char * name)
{
	int i = 0;
	int pos = 0;

	while (name[i] != 0)
	{
		if (name[i] == '/')
			pos = i;

		i++;
	}

	if (name[pos] == '/')
		pos++;

	return name + pos;
}


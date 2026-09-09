/*
 * e2_procfs_main.c
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
#include <linux/module.h>
#include <linux/init.h>

MODULE_DESCRIPTION("e2_procfs");
MODULE_LICENSE("GPL"); // Or "GPL v2", "Dual BSD/GPL", etc.

struct ProcStructure_s e2Proc[] =
{
	{cProcEntry, "progress"                                                         , NULL, e2procfs_progress_show, e2procfs_progress_write, NULL, ""},

	{cProcEntry, "bus/nim_sockets"                                                  , NULL, e2procfs_nim_sockets_show, e2procfs_nim_sockets_write, NULL, ""},
	{cProcDir  , "stb"                                                              , NULL, NULL, NULL, NULL, ""},
	{cProcDir  , "stb/audio"                                                        , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/audio/ac3"                                                    , NULL, e2procfs_ac3_show, e2procfs_ac3_write, NULL, ""},
	{cProcEntry, "stb/audio/audio_delay_pcm"                                        , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/audio/audio_delay_bitstream"                                  , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/audio/j1_mute"                                                , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/audio/ac3_choices"                                            , NULL, e2procfs_ac3choices_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/dts"                                                    , NULL, e2procfs_dts_show, e2procfs_dts_write, NULL, ""},
	{cProcEntry, "stb/audio/dts_choices"                                            , NULL, e2procfs_dtschoices_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/aac"                                                    , NULL, e2procfs_aac_show, e2procfs_aac_write, NULL, ""},
	{cProcEntry, "stb/audio/aac_choices"                                            , NULL, e2procfs_aacchoices_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/avl"                                                    , NULL, e2procfs_avl_show, e2procfs_avl_write, NULL, ""},
	{cProcEntry, "stb/audio/avl_choices"                                            , NULL, e2procfs_avlchoices_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/autovolumelevel"                                        , NULL, e2procfs_autovolumelevel_show, e2procfs_aac_write, NULL, ""},
	{cProcEntry, "stb/audio/autovolumelevel_choices"                                , NULL, e2procfs_autovolumelevelchoices_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/multichannel_pcm"                                       , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/audio/3dsurround"                                             , NULL, e2procfs_3dsurround_show, e2procfs_3dsurround_write, NULL, ""},
	{cProcEntry, "stb/audio/3dsurround_choices"                                     , NULL, e2procfs_3dsurroundchoices_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/3dsurround_softlimiter_choices"                         , NULL, e2procfs_3dsurround_softlimiterchoices_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/3dsurround_softlimiter"                                 , NULL, e2procfs_3dsurround_softlimiter_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/3d_surround"                                            , NULL, e2procfs_3d_surround_show, e2procfs_3d_surround_write, NULL, ""},
	{cProcEntry, "stb/audio/3d_surround_choices"                                    , NULL, e2procfs_3d_surroundchoices_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/3d_surround_speaker_position"                           , NULL, e2procfs_3d_surround_speaker_position_show, NULL, NULL, ""},
	{cProcEntry, "stb/audio/3d_surround_speaker_position_choices"                   , NULL, e2procfs_3d_surround_speaker_positionchoices_show, NULL, NULL, ""},

	{cProcDir  , "stb/frontend"                                                     , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/dvr_source_offset"                                   , NULL, NULL, NULL, NULL, ""},

	{cProcDir  , "stb/frontend/0"                                                   , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/0/mode"                                              , NULL, e2procfs_frontend_mode_show, e2procfs_frontend_mode_write, NULL, ""},
	{cProcEntry, "stb/frontend/0/t2mi"                                              , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/0/t2mirawmode"                                       , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/0/lnb_sense"                                         , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/0/static_current_limiting"                           , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/0/active_antenna_power"                              , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/0/rf_switch"                                         , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/0/use_scpc_optimized_search_range"                   , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/0/tone_amplitude"                                    , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/0/fbc_id"                                            , NULL, NULL, NULL, NULL, ""},

	{cProcDir  , "stb/frontend/1"                                                   , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/1/mode"                                              , NULL, e2procfs_frontend_mode_show, e2procfs_frontend_mode_write, NULL, ""},
	{cProcEntry, "stb/frontend/1/t2mi"                                              , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/1/t2mirawmode"                                       , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/1/lnb_sense"                                         , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/1/static_current_limiting"                           , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/1/active_antenna_power"                              , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/1/rf_switch"                                         , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/1/use_scpc_optimized_search_range"                   , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/1/tone_amplitude"                                    , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/frontend/1/fbc_id"                                            , NULL, NULL, NULL, NULL, ""},

	{cProcDir  , "stb/info"                                                         , NULL, NULL, NULL, NULL, ""},
	{cProcEntry, "stb/info/boxtype"                                                 , NULL, e2procfs_info_model_show, NULL, NULL, ""},
	{cProcEntry, "stb/info/chipset"                                                 , NULL, e2procfs_info_chipset_show, NULL, NULL, ""},
	{cProcEntry, "stb/info/vumodel"                                                 , NULL, e2procfs_info_model_show, NULL, NULL, ""},
	{cProcEntry, "stb/info/version"                                                 , NULL, e2procfs_info_chipset_show, NULL, NULL, ""},
	{cProcEntry, "stb/info/board_revision"                                          , NULL, e2procfs_info_brand_show, NULL, NULL, ""},
	{cProcEntry, "stb/info/brandname"                                               , NULL, e2procfs_info_brand_show, NULL, NULL, ""},

	{cProcDir  , "stb/video"                                                        , NULL, NULL, NULL, NULL, ""},
	// Конец массива (добавлено для корректного синтаксиса):
	{0, NULL, NULL, NULL, NULL, NULL, ""}
};


/*
 * This file is part of arduino-cli.
 *
 * arduino-cli is free software; you can redistribute it and/or modify
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
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * As a special exception, you may use this file as part of a free software
 * library without restriction.  Specifically, if other files instantiate
 * templates or use macros or inline functions from this file, or you compile
 * this file and link it with other files to produce an executable, this
 * file does not by itself cause the resulting executable to be covered by
 * the GNU General Public License.  This exception does not however
 * invalidate any other reasons why the executable file might be covered by
 * the GNU General Public License.
 *
 * Copyright 2017 ARDUINO AG (http://www.arduino.cc/)
 */

package createClient

import (
	"encoding/base64"
	"io/ioutil"
	"path/filepath"

	"github.com/bcmi-labs/arduino-modules/sketches"
)

// A file saved on the virtual filesystem
type File struct {
	// The contents of the file, encoded in base64
	Data *string `form:"data,omitempty" json:"data,omitempty" xml:"data,omitempty"`
	// The name of the file
	Name string `form:"name" json:"name" xml:"name"`
}

// A program meant to be uploaded onto a board
type Sketch struct {
	// The name of the sketch
	Name string `form:"name" json:"name" xml:"name"`
	// The other files contained in the sketch
	Files []*File `form:"files,omitempty" json:"files,omitempty" xml:"files,omitempty"`
	// The folder path where the sketch is saved
	Folder *string `form:"folder,omitempty" json:"folder,omitempty" xml:"folder,omitempty"`
	// The main file of the sketch
	Ino      *File           `form:"ino" json:"ino" xml:"ino"`
	Metadata *SketchMetadata `form:"metadata,omitempty" json:"metadata,omitempty" xml:"metadata,omitempty"`
	// The username of the owner of the sketch
	Owner *string `form:"owner,omitempty" json:"owner,omitempty" xml:"owner,omitempty"`
	// A private sketch is only visible to its owner.
	Private bool `form:"private" json:"private" xml:"private"`
	// A list of links to hackster tutorials.
	Tutorials []string `form:"tutorials,omitempty" json:"tutorials,omitempty" xml:"tutorials,omitempty"`
	// A list of tags. The builtin tag means that it's a builtin example.
	Types []string `form:"types,omitempty" json:"types,omitempty" xml:"types,omitempty"`
}

//ConvertFrom converts from a local sketch to an Arduino Create sketch.
func ConvertFrom(sketch sketches.Sketch) *Sketch {
	_, inoPath := filepath.Split(sketch.Ino.Path)
	content, err := ioutil.ReadFile(filepath.Join(sketch.FullPath, inoPath))
	if err != nil {
		return nil
	}

	ino := base64.StdEncoding.EncodeToString(content)
	ret := Sketch{
		Name:   sketch.Name,
		Folder: &sketch.Path,
		Ino: &File{
			Data: &ino,
			Name: sketch.Ino.Name,
		},
		Private:   sketch.Private,
		Tutorials: sketch.Tutorials,
		Types:     sketch.Types,
		Metadata:  ConvertMetadataFrom(sketch.Metadata),
	}
	ret.Files = make([]*File, len(sketch.Files))
	for i, f := range sketch.Files {
		if f.Name == "sketch.json" { //skipping sketch.json file, since it is Metadata of the sketch
			continue
		}
		_, filePath := filepath.Split(f.Path)
		content, err := ioutil.ReadFile(filepath.Join(sketch.FullPath, filePath))
		if err != nil {
			return nil
		}

		data := base64.StdEncoding.EncodeToString(content)
		ret.Files[i] = &File{
			Data: &data,
			Name: f.Name,
		}
	}
	return &ret
}

// SketchMetadata user type.
type SketchMetadata struct {
	CPU          *SketchMetadataCPU   `form:"cpu,omitempty" json:"cpu,omitempty" xml:"cpu,omitempty"`
	IncludedLibs []*SketchMetadataLib `form:"included_libs,omitempty" json:"included_libs,omitempty" xml:"included_libs,omitempty"`
}

func ConvertMetadataFrom(metadata *sketches.Metadata) *SketchMetadata {
	if metadata == nil {
		return nil
	}
	network := metadata.CPU.Type == "network"
	ret := SketchMetadata{
		CPU: &SketchMetadataCPU{
			Fqbn:    &metadata.CPU.Fqbn,
			Name:    &metadata.CPU.Name,
			Network: &network,
			Port:    &metadata.CPU.Port,
		},
	}
	ret.IncludedLibs = make([]*SketchMetadataLib, len(metadata.IncludedLibs))
	for i, lib := range metadata.IncludedLibs {
		ret.IncludedLibs[i] = &SketchMetadataLib{
			Name:    &lib.Name,
			Version: &lib.Version,
		}
	}

	return &ret
}

// The board associated with the sketch
type SketchMetadataCPU struct {
	// The fqbn of the board
	Fqbn *string `form:"fqbn,omitempty" json:"fqbn,omitempty" xml:"fqbn,omitempty"`
	// The name of the board
	Name *string `form:"name,omitempty" json:"name,omitempty" xml:"name,omitempty"`
	// Requires an upload via network
	Network *bool `form:"network,omitempty" json:"network,omitempty" xml:"network,omitempty"`
	// The port of the board
	Port *string `form:"port,omitempty" json:"port,omitempty" xml:"port,omitempty"`
}

// A library associated with the sketch
type SketchMetadataLib struct {
	// The name of the library
	Name *string `form:"name,omitempty" json:"name,omitempty" xml:"name,omitempty"`
	// The version of the library
	Version *string `form:"version,omitempty" json:"version,omitempty" xml:"version,omitempty"`
}

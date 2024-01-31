package main

import (
	"encoding/hex"
	"errors"
	// "strings"
	"crypto/md5"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// Sub2RelayContract contract for handling IoTDatas
type Sub2RelayContract struct {
	contractapi.Contract
}

//toChaincodeArgs generates args for chaincode invoke
func toChaincodeArgs(args ...string) [][]byte {
	bargs := make([][]byte, len(args))
	for i, arg := range args {
		bargs[i] = []byte(arg)
	}
	return bargs
}

//performHash using hash function to compress data
func performHash(raw []byte) string {
	md5Ctx := md5.New()
    md5Ctx.Write(raw)
    cipherStr := hex.EncodeToString(md5Ctx.Sum(nil))
	return cipherStr
}


func (cc *Sub2RelayContract) UploadOneData(ctx CustomTransactionContextInterface, id string, from string, newid string) error {

	queryArgs := toChaincodeArgs("GetIoTData", id)
	response := ctx.GetStub().InvokeChaincode("subGeneralCC", queryArgs, "sub-channel")

	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}


	rawBytes := []byte(response.Payload)
	if rawBytes == nil {
		return errors.New("InvokeChaincode returns nil!")
	}

	//hash
	payload := performHash(rawBytes)

	newID := newid
	writeArgs := toChaincodeArgs("UploadIoTData", newID, from, payload)
	response = ctx.GetStub().InvokeChaincode("relayGeneralCC", writeArgs, "relay-channel")

	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}

	return nil
}

func (cc *Sub2RelayContract) UploadAllData(ctx CustomTransactionContextInterface, from string, newid string) error {

	queryArgs := toChaincodeArgs("GetAllIoTData")
	response := ctx.GetStub().InvokeChaincode("subGeneralCC", queryArgs, "sub-channel")
	
	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}

	rawBytes := []byte(response.Payload)
	if rawBytes == nil {
		return errors.New("InvokeChaincode error!")
	}
	payload := performHash(rawBytes)

	newID := newid

	writeArgs := toChaincodeArgs("UploadIoTData", newID, from, payload)
	response = ctx.GetStub().InvokeChaincode("relayGeneralCC", writeArgs, "relay-channel")

	if response.Status != 200 {
		errors.New("InvokeChaincode return " + response.Message)
	}


	return nil
}

